-- ==========================================
-- M_APPLICATION_FIELDテーブルのfield_type制約を修正
-- チェックボックスタイプ('checkbox')を追加
-- ==========================================

-- 既存のCHECK制約を削除
ALTER TABLE M_APPLICATION_FIELD DROP CONSTRAINT CHK_FIELD_TYPE;

-- 新しいCHECK制約を作成（'checkbox'を追加、'resource_select'を削除）
ALTER TABLE M_APPLICATION_FIELD
ADD CONSTRAINT CHK_FIELD_TYPE
CHECK (field_type IN ('text', 'number', 'date', 'select', 'datalist', 'textarea', 'checkbox'));

-- 確認
SELECT constraint_name, search_condition
FROM user_constraints
WHERE table_name = 'M_APPLICATION_FIELD'
  AND constraint_name = 'CHK_FIELD_TYPE';
