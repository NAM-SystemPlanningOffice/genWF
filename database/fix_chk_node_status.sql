-- T_WORKFLOW_NODE_INSTANCE の node_status 制約に 'withdrawn' を追加する修正SQL

-- 既存の制約を削除
ALTER TABLE T_WORKFLOW_NODE_INSTANCE DROP CONSTRAINT CHK_NODE_STATUS;

-- 新しい制約を追加（'withdrawn' を含む）
ALTER TABLE T_WORKFLOW_NODE_INSTANCE ADD CONSTRAINT CHK_NODE_STATUS
    CHECK (node_status IN ('waiting', 'pending', 'approved', 'rejected', 'returned', 'skipped', 'failed', 'withdrawn'));
