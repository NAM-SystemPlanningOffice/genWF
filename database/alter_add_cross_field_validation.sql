-- ==========================================
-- M_VALIDATION_RULEテーブルのルールタイプに'cross_field'を追加
-- クロスフィールドバリデーション（複数フィールド間の条件チェック）対応
-- ==========================================

-- 既存のCHECK制約を削除
ALTER TABLE M_VALIDATION_RULE DROP CONSTRAINT CHK_VALID_RULE_TYPE;

-- 新しいCHECK制約を作成（'cross_field'を追加）
ALTER TABLE M_VALIDATION_RULE
ADD CONSTRAINT CHK_VALID_RULE_TYPE CHECK (rule_type IN (
    'required',
    'minlength',
    'maxlength',
    'pattern',
    'starts_with',
    'ends_with',
    'contains',
    'equals',
    'email',
    'numeric',
    'min_value',
    'max_value',
    'date_format',
    'future_date',
    'past_date',
    'exists_in_table',
    'unique_in_table',
    'custom_query',
    'cross_field'
));

-- 確認
SELECT constraint_name, search_condition
FROM user_constraints
WHERE table_name = 'M_VALIDATION_RULE'
  AND constraint_name = 'CHK_VALID_RULE_TYPE';

-- ==========================================
-- サンプル: クロスフィールドバリデーションルールの登録例
-- ==========================================
/*
-- 例: チェックボックス依存関係チェック
-- value=='Y'は無条件OK、value=='N'の場合は(field_A=='Y' OR field_B=='Y') AND field_C=='Y'が必要
INSERT INTO M_VALIDATION_RULE (
    validation_rule_id,
    rule_code,
    rule_name,
    rule_type,
    rule_parameter,
    error_message,
    description,
    is_active
) VALUES (
    SEQ_VALIDATION_RULE.NEXTVAL,
    'checkbox_dependency_example',
    'チェックボックス依存関係チェック例',
    'cross_field',
    '{"condition": "value == ''Y'' or ((field_1001 == ''Y'' or field_1002 == ''Y'') and field_1003 == ''Y'')", "fields": [1001, 1002, 1003]}',
    'フィールドAまたはBが''Y''、かつフィールドCが''Y''の場合のみ、このフィールドを設定できます',
    'クロスフィールドバリデーションのサンプル',
    'Y'
);

-- フィールドに割り当て（例: field_id=1004に適用）
INSERT INTO M_FIELD_VALIDATION (
    field_validation_id,
    field_id,
    validation_rule_id,
    check_order,
    apply_on_create,
    apply_on_modify,
    is_active
) VALUES (
    SEQ_FIELD_VALIDATION.NEXTVAL,
    1004,
    (SELECT validation_rule_id FROM M_VALIDATION_RULE WHERE rule_code = 'checkbox_dependency_example'),
    10,
    'Y',
    'Y',
    'Y'
);
*/
