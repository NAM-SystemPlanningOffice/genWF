-- ==========================================
-- 自動処理関連テーブルの削除
-- (これらは自動処理システム側で管理)
-- ==========================================

-- 外部キー制約を持つテーブルから削除
DROP TABLE T_AUTO_PROCESS_LOG CASCADE CONSTRAINTS;

-- マスタテーブルを削除
DROP TABLE M_AUTO_PROCESS_DEFINITION CASCADE CONSTRAINTS;

-- シーケンスを削除
DROP SEQUENCE SEQ_AUTO_PROCESS_DEFINITION;
DROP SEQUENCE SEQ_AUTO_PROCESS_LOG;

-- 確認
SELECT table_name
FROM user_tables
WHERE table_name IN ('M_AUTO_PROCESS_DEFINITION', 'T_AUTO_PROCESS_LOG');

-- 結果が0行であれば削除成功
