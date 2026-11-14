-- 每日 01:00 对账（CronJob 跑 psql）；任一查询结果非空就告警，并记进护栏指标。

-- C1 余额 ≠ 流水之和（包括有流水但没有账户的情况）
SELECT COALESCE(a.user_id, l.user_id) AS user_id, a.balance, l.sum_amount
FROM points_account a
FULL JOIN (SELECT user_id, SUM(amount) AS sum_amount FROM points_ledger GROUP BY user_id) l USING (user_id)
WHERE COALESCE(a.balance, 0) <> COALESCE(l.sum_amount, 0);

-- C2 同一用户同一签到日期，基础奖励超过 1 条
-- （按 checkin_record.checkin_date 分组，不用流水 created_at 换算日期，避免跨零点误报）
SELECT c.user_id, c.checkin_date, COUNT(*)
FROM points_ledger l
JOIN checkin_record c ON l.biz_type = 'CHECKIN' AND l.biz_id = c.id::text AND l.user_id = c.user_id
WHERE l.type = 'CHECKIN_BASE'
GROUP BY c.user_id, c.checkin_date HAVING COUNT(*) > 1;

-- C3 签到记录和流水金额对不上（漏发、多发）
SELECT c.id, c.user_id, c.points_base + c.points_bonus AS expected, COALESCE(SUM(l.amount), 0) AS actual
FROM checkin_record c
LEFT JOIN points_ledger l ON l.biz_type = 'CHECKIN' AND l.biz_id = c.id::text
WHERE c.checkin_date = (now() AT TIME ZONE 'Asia/Shanghai')::date - 1
GROUP BY c.id, c.user_id, c.points_base, c.points_bonus
HAVING c.points_base + c.points_bonus <> COALESCE(SUM(l.amount), 0);

-- C4 balance_after 链路断裂（前一条的 balance_after + 本条 amount ≠ 本条 balance_after）
SELECT user_id, id FROM (
  SELECT user_id, id, amount, balance_after,
         LAG(balance_after, 1, 0::bigint) OVER (PARTITION BY user_id ORDER BY id) AS prev  -- 同一用户写入被行锁串行化，id 顺序就是发放顺序
  FROM points_ledger
) t WHERE prev + amount <> balance_after;
