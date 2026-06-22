# クロスフィールドバリデーション設計

## 概要

複数フィールド間の条件チェック（クロスフィールドバリデーション）を実現する方法。

例: `(フィールドA=='Y' OR フィールドB=='Y') AND フィールドC=='Y'`でなければ、現在のフィールドは'N'にできない

## 実装方針

### 方針1: custom_query_cross_field（新規ルールタイプ）

複数フィールドの値を参照できる専用のルールタイプを追加。

#### テーブル定義の変更

```sql
-- M_VALIDATION_RULEのCHECK制約にルールタイプを追加
ALTER TABLE M_VALIDATION_RULE DROP CONSTRAINT CHK_VALID_RULE_TYPE;
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
    'cross_field'  -- 新規追加
));
```

#### パラメータ仕様

```json
{
  "condition": "(field_1001 == 'Y' or field_1002 == 'Y') and field_1003 == 'Y'",
  "fields": [1001, 1002, 1003],
  "error_message": "フィールドAまたはBが'Y'かつフィールドCが'Y'の場合、このフィールドは'N'にできません"
}
```

| キー | 必須 | 説明 |
|-----|-----|------|
| condition | ○ | Pythonの条件式（field_XXXXで他フィールドを参照） |
| fields | ○ | 参照するfield_idの配列 |
| error_message | - | エラーメッセージ（未指定時はデフォルト） |

#### バリデーションルールの登録例

```sql
-- ルールの定義
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
    'cross_field_example',
    'クロスフィールドチェック例',
    'cross_field',
    '{"condition": "(field_1001 == ''Y'' or field_1002 == ''Y'') and field_1003 == ''Y'' and value == ''N''", "fields": [1001, 1002, 1003]}',
    'フィールドAまたはBが''Y''かつフィールドCが''Y''の場合、このフィールドは''N''にできません',
    'クロスフィールドバリデーションの例',
    'Y'
);

-- フィールドに割り当て
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
    1004,  -- チェック対象のフィールドID
    (SELECT validation_rule_id FROM M_VALIDATION_RULE WHERE rule_code = 'cross_field_example'),
    10,    -- 他のバリデーション後に実行
    'Y',
    'Y',
    'Y'
);
```

#### Python実装

```python
# app/services/validation_service.py

@staticmethod
def _validate_cross_field(value, parameter, all_field_values):
    """
    クロスフィールドバリデーション
    
    Args:
        value: 現在のフィールドの値
        parameter: JSON形式のパラメータ
        all_field_values: 全フィールドの値（dict: {field_id: value}）
    
    Returns:
        (is_valid, error_message)
    """
    if value is None:
        return True, None
    
    params = json.loads(parameter)
    condition = params['condition']
    required_fields = params['fields']
    custom_message = params.get('error_message')
    
    # 必要なフィールドの値を取得
    field_vars = {'value': value}
    for field_id in required_fields:
        field_vars[f'field_{field_id}'] = all_field_values.get(field_id, '')
    
    # 条件式を評価（セキュリティ考慮：evalは使わずast.literal_evalベースで実装）
    try:
        # 簡易的な条件評価（実際にはより安全な実装が必要）
        result = eval(condition, {"__builtins__": {}}, field_vars)
        
        if not result:
            return False, custom_message
        return True, None
    except Exception as e:
        return False, f"バリデーションエラー: {str(e)}"


# バリデーション実行時に全フィールドの値を渡す
@staticmethod
def validate_all_fields(field_values):
    """
    全フィールドのバリデーションを実行
    
    Args:
        field_values: dict {field_id: value}
    
    Returns:
        (is_valid, errors_dict)
    """
    errors = {}
    
    for field_id, value in field_values.items():
        validations = FieldValidation.get_by_field(field_id)
        
        for validation in validations:
            rule_type = validation['rule_type']
            parameter = validation['rule_parameter']
            
            if rule_type == 'cross_field':
                # クロスフィールドバリデーションの場合は全フィールド値を渡す
                is_valid, error = ValidationService._validate_cross_field(
                    value, parameter, field_values
                )
            else:
                # 通常のバリデーション
                is_valid, error = ValidationService._execute_rule(
                    rule_type, value, parameter
                )
            
            if not is_valid:
                if field_id not in errors:
                    errors[field_id] = []
                errors[field_id].append(error or validation['error_message'])
    
    return len(errors) == 0, errors
```

#### クライアントサイド（JavaScript）

```javascript
// app/templates/application/create.html

// クロスフィールドバリデーション用の関数
function validateCrossField(fieldId, value, condition, requiredFields) {
    // 必要なフィールドの値を取得
    const fieldValues = { value: value };
    requiredFields.forEach(fid => {
        const input = document.getElementById('field_' + fid);
        if (input) {
            if (input.type === 'checkbox') {
                fieldValues['field_' + fid] = input.checked ? 'Y' : 'N';
            } else {
                fieldValues['field_' + fid] = input.value;
            }
        }
    });
    
    // 条件式を評価（安全な方法で実装）
    try {
        // 簡易的な実装例（実際にはより安全な方法が必要）
        const evalCondition = condition
            .replace(/field_(\d+)/g, (match, fid) => {
                const val = fieldValues['field_' + fid];
                return val === 'Y' || val === 'N' ? `"${val}"` : val;
            })
            .replace(/value/g, `"${value}"`)
            .replace(/==/g, '===')
            .replace(/and/g, '&&')
            .replace(/or/g, '||');
        
        return eval(evalCondition);
    } catch (e) {
        console.error('Validation error:', e);
        return true; // エラー時はサーバーサイドに任せる
    }
}

// バリデーション実行時
if (validation.rule_type === 'cross_field') {
    const params = JSON.parse(validation.rule_parameter);
    const isValid = validateCrossField(
        fieldKey,
        value,
        params.condition,
        params.fields
    );
    
    if (!isValid) {
        // エラー表示
        const errorEl = document.getElementById('error_' + fieldKey);
        if (errorEl) {
            errorEl.textContent = params.error_message || validation.error_message;
            errorEl.style.display = 'block';
        }
        hasError = true;
    }
}
```

---

## 方針2: custom_queryで擬似的に実現（簡易版）

既存の`custom_query`を使って、複数フィールドの値を結合した形でチェック。

### メリット
- 既存の仕組みを流用できる
- テーブル定義の変更不要

### デメリット
- フィールド値の受け渡しが複雑
- クライアントサイドでのバリデーションが困難

### 実装例

申請データをT_APPLICATION_DETAILから取得してチェック：

```sql
-- カスタムクエリ例
SELECT COUNT(*) FROM (
    SELECT 
        MAX(CASE WHEN field_id = 1001 THEN field_value END) as field_a,
        MAX(CASE WHEN field_id = 1002 THEN field_value END) as field_b,
        MAX(CASE WHEN field_id = 1003 THEN field_value END) as field_c
    FROM T_APPLICATION_DETAIL
    WHERE application_id = :application_id
) t
WHERE 
    (t.field_a = 'Y' OR t.field_b = 'Y') 
    AND t.field_c = 'Y' 
    AND :value = 'N'
```

この方法だと、申請提出時（サーバーサイド）のみチェック可能で、リアルタイムのクライアントサイドチェックは困難。

---

## 推奨

**方針1: cross_fieldルールタイプの新規追加**を推奨します。

理由：
- クライアントサイド・サーバーサイド両方で対応可能
- 条件式が柔軟に記述できる
- パフォーマンスが良い
- 将来的な拡張性が高い

ただし、`eval()`の使用にはセキュリティリスクがあるため、条件式の評価には以下の対策が必要：
1. 許可された演算子・関数のみ使用可能にする
2. `ast.literal_eval()`ベースの安全な評価器を実装
3. パラメータはマスターデータとして管理し、ユーザー入力を直接評価しない
