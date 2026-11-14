-- 账户：余额快照，和流水在同一事务里更新
CREATE TABLE points_account (
  user_id     VARCHAR(64) PRIMARY KEY,
  balance     BIGINT      NOT NULL DEFAULT 0 CHECK (balance >= 0),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 签到记录：一人一天一条
CREATE TABLE checkin_record (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id       VARCHAR(64) NOT NULL,
  checkin_date  DATE        NOT NULL,                 -- 北京时间自然日，由应用层计算（D5）
  streak_days   INT         NOT NULL CHECK (streak_days >= 1),
  cycle_day     SMALLINT    NOT NULL CHECK (cycle_day BETWEEN 1 AND 7),
  points_base   INT         NOT NULL CHECK (points_base >= 0),
  points_bonus  INT         NOT NULL CHECK (points_bonus >= 0),
  rule_version  VARCHAR(32) NOT NULL,
  request_id    UUID        NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_checkin_user_date    UNIQUE (user_id, checkin_date),   -- 唯一防重依据（R6）；也用于「取最近一条」的倒序扫描
  CONSTRAINT uq_checkin_user_request UNIQUE (user_id, request_id)      -- 幂等重放（D4）
);

-- 积分流水：只追加
CREATE TABLE points_ledger (
  id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id        VARCHAR(64) NOT NULL,
  type           VARCHAR(32) NOT NULL CHECK (type IN ('CHECKIN_BASE','CHECKIN_STREAK_BONUS','REDEEM','ADJUST','EXPIRE')),
  amount         BIGINT      NOT NULL CHECK (amount <> 0),
  balance_after  BIGINT      NOT NULL CHECK (balance_after >= 0),
  biz_type       VARCHAR(32) NOT NULL,                 -- 本期固定 'CHECKIN'
  biz_id         VARCHAR(64) NOT NULL,                 -- checkin_record.id 转成文本；以后兑换订单号等也能放
  remark         VARCHAR(128) NOT NULL DEFAULT '',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_ledger_biz UNIQUE (biz_type, biz_id, type)  -- 同一笔业务、同一类型只能发一次
);
CREATE INDEX idx_ledger_user_time ON points_ledger (user_id, created_at DESC, id DESC);  -- 游标分页

-- 只追加：禁止 UPDATE / DELETE
CREATE FUNCTION points_ledger_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'points_ledger is append-only';
END $$;
CREATE TRIGGER trg_points_ledger_append_only
  BEFORE UPDATE OR DELETE ON points_ledger
  FOR EACH ROW EXECUTE FUNCTION points_ledger_append_only();
-- 部署时：应用账号 GRANT SELECT, INSERT ON points_ledger；不授予 UPDATE / DELETE / TRUNCATE（由 SRE 在上线单里执行）
