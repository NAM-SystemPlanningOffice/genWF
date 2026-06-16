-- ==========================================
-- T_WORKFLOW_NODE_INSTANCE に failed ステータスを追加
-- ==========================================

-- CHK_NODE_STATUS 制約を削除
ALTER TABLE T_WORKFLOW_NODE_INSTANCE
DROP CONSTRAINT CHK_NODE_STATUS;

-- failed を含む新しい制約を追加
ALTER TABLE T_WORKFLOW_NODE_INSTANCE
ADD CONSTRAINT CHK_NODE_STATUS
CHECK (node_status IN ('waiting', 'pending', 'approved', 'rejected', 'returned', 'skipped', 'failed'));

-- コメント追加
COMMENT ON COLUMN T_WORKFLOW_NODE_INSTANCE.node_status IS 'ノードステータス: waiting(待機), pending(処理中), approved(承認), rejected(却下), returned(差戻), skipped(スキップ), failed(自動処理失敗)';

-- 確認
SELECT constraint_name, search_condition
FROM user_constraints
WHERE table_name = 'T_WORKFLOW_NODE_INSTANCE'
  AND constraint_type = 'C'
  AND constraint_name = 'CHK_NODE_STATUS';
