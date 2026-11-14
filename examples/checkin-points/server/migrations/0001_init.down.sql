-- 回滚：只能在灰度前、表里没有真实用户数据时执行。一旦有真实发放，禁止 DROP（积分是资产）。
-- DROP 属于删除数据库操作，必须用户确认后才能执行。
DROP TABLE IF EXISTS points_ledger;
DROP FUNCTION IF EXISTS points_ledger_append_only();
DROP TABLE IF EXISTS checkin_record;
DROP TABLE IF EXISTS points_account;
