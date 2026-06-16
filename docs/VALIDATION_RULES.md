# バリデーションルール仕様書

## 概要

本システムでは、申請フィールドに対して柔軟なバリデーションルールを設定できます。
バリデーションルールは`M_VALIDATION_RULE`テーブルで定義され、`M_FIELD_VALIDATION`テーブルでフィールドに割り当てられます。

**パラメータ設計方針**:
- 単一のパラメータの場合は**単純な文字列**
- 複数のパラメータキーが必要な場合のみ**JSON形式**

---

## ルールタイプ一覧表

| # | Rule Type | チェック内容 | パラメータ | パラメータ形式 | 例 |
|---|-----------|------------|-----------|--------------|---|
| 1 | required | 必須入力 | 不要 | - | - |
| 2 | minlength | 最小文字数 | 必須 | 数値文字列 | `"5"` |
| 3 | maxlength | 最大文字数 | 必須 | 数値文字列 | `"100"` |
| 4 | pattern | 正規表現パターン | 必須 | 正規表現文字列 | `"^[A-Z][0-9]{5}$"` |
| 5 | starts_with | 前方一致 | 必須 | 文字列 | `"USER_"` |
| 6 | ends_with | 後方一致 | 必須 | 文字列 | `"@example.com"` |
| 7 | contains | 部分一致 | 必須 | 文字列 | `"test"` |
| 8 | equals | 完全一致 | 必須 | 文字列 | `"APPROVED"` |
| 9 | email | メールアドレス形式 | 不要 | - | - |
| 10 | numeric | 数値形式 | 不要 | - | - |
| 11 | min_value | 最小値 | 必須 | 数値文字列 | `"0"` |
| 12 | max_value | 最大値 | 必須 | 数値文字列 | `"999999"` |
| 13 | date_format | 日付形式 | 必須 | フォーマット文字列 | `"YYYY-MM-DD"` |
| 14 | future_date | 未来日付 | 不要 | - | - |
| 15 | past_date | 過去日付 | 不要 | - | - |
| 16 | exists_in_table | テーブル存在 | 必須 | JSON（複数キー） | `{"table": "M_DEPT", "column": "dept_cd"}` |
| 17 | unique_in_table | テーブル一意性 | 必須 | JSON（複数キー） | `{"table": "M_USER", "column": "email"}` |
| 18 | custom_query | カスタムSQL | 必須 | JSON（複数キー） | `{"query": "...", "expect": "0"}` |
| 19 | cross_field | クロスフィールド | 必須 | JSON（複数キー） | `{"condition": "value == 'Y' or ...", "fields": [1001, 1002]}` |

---

## パラメータ詳細

### 1. パラメータ不要（NULL）

| Rule Type | チェック内容 |
|-----------|------------|
| required | 値が空でないことを確認 |
| email | 標準的なメールアドレス形式 |
| numeric | 数値のみで構成されているか |
| future_date | 本日以降の日付のみ許可 |
| past_date | 本日以前の日付のみ許可 |

### 2. 数値・範囲系（単純な文字列）

| Rule Type | パラメータ | 説明 | 例 |
|-----------|----------|------|---|
| minlength | 数値文字列 | 最小文字数 | `"5"` → 5文字以上 |
| maxlength | 数値文字列 | 最大文字数 | `"100"` → 100文字以内 |
| min_value | 数値文字列 | 最小値 | `"0"` → 0以上 |
| max_value | 数値文字列 | 最大値 | `"999999"` → 999999以下 |

### 3. 文字列パターン系（単純な文字列）

| Rule Type | パラメータ | 説明 | 例 |
|-----------|----------|------|---|
| pattern | 正規表現文字列 | 正規表現に一致するか | `"^[A-Z][0-9]{5}$"` |
| starts_with | 文字列 | 指定文字列で始まるか | `"USER_"` |
| ends_with | 文字列 | 指定文字列で終わるか | `"@example.com"` |
| contains | 文字列 | 指定文字列を含むか | `"test"` |
| equals | 文字列 | 指定文字列と完全一致するか | `"APPROVED"` |

**patternの正規表現例**:
- ユーザーコード（英字1文字+5桁数字）: `"^[A-Z][0-9]{5}$"`
- 電話番号（ハイフン区切り）: `"^[0-9]{2,4}-[0-9]{2,4}-[0-9]{3,4}$"`
- 郵便番号: `"^[0-9]{3}-[0-9]{4}$"`

### 4. 日付形式（単純な文字列）

| Rule Type | パラメータ | 説明 | 例 |
|-----------|----------|------|---|
| date_format | フォーマット文字列 | 指定フォーマットに一致するか | `"YYYY-MM-DD"` |

**よくある日付フォーマット**:
- `"YYYY-MM-DD"` → 2026-05-22
- `"YYYY/MM/DD"` → 2026/05/22
- `"YYYYMMDD"` → 20260522
- `"DD/MM/YYYY"` → 22/05/2026

### 5. データベース系（JSON形式）

#### exists_in_table（テーブル内存在チェック）

```json
{
  "table": "nam_user_admin.e_imdb2_users",
  "column": "department_cd",
  "condition": "is_active='Y'"
}
```

| キー | 必須 | 説明 |
|-----|-----|------|
| table | ○ | チェック対象のテーブル名（スキーマ含む可） |
| column | ○ | チェック対象のカラム名 |
| condition | - | 追加のWHERE条件（例: `is_active='Y'`） |

#### unique_in_table（テーブル内一意性チェック）

```json
{
  "table": "nam_user_admin.gmail_group_setting",
  "column": "name",
  "key_column": "email"
}
```

| キー | 必須 | 説明 |
|-----|-----|------|
| table | ○ | チェック対象のテーブル名 |
| column | ○ | チェック対象のカラム名 |
| key_column | - | 主キーカラム名（デフォルト: `resource_id`）<br>編集時に自分自身を除外するために使用 |

#### custom_query（カスタムSQLクエリ）

```json
{
  "query": "SELECT COUNT(*) FROM T_APPLICATION WHERE applicant_user_id = :value AND application_status = 'draft'",
  "expect": "0",
  "message": "下書きの申請が既に存在します"
}
```

| キー | 必須 | 説明 |
|-----|-----|------|
| query | ○ | 実行するSQLクエリ（:valueで入力値を参照） |
| expect | ○ | 期待する結果（通常は "0"） |
| message | - | カスタムエラーメッセージ |

#### cross_field（クロスフィールドバリデーション）

**単一レコード申請のみ対応**

複数フィールド間の条件チェック。他のフィールドの値を参照して条件を評価。

```json
{
  "condition": "value == 'Y' or ((field_1001 == 'Y' or field_1002 == 'Y') and field_1003 == 'Y')",
  "fields": [1001, 1002, 1003]
}
```

| キー | 必須 | 説明 |
|-----|-----|------|
| condition | ○ | 条件式（Python/JavaScript形式）<br>`value`: 現在のフィールドの値<br>`field_XXXX`: 他のフィールドの値（XXXXはfield_id） |
| fields | ○ | 参照するfield_idの配列 |

**条件式の記法**:
- 比較演算子: `==`, `!=`, `>`, `<`, `>=`, `<=`
- 論理演算子: `and`, `or`（JavaScriptでは`&&`, `||`に自動変換）
- 括弧: `(`, `)`で優先順位を制御

**例**:
```json
{
  "condition": "value == 'Y' or ((field_1001 == 'Y' or field_1002 == 'Y') and field_1003 == 'Y')",
  "fields": [1001, 1002, 1003]
}
```
↑「valueが'Y'なら無条件OK、'N'の場合は(field_1001が'Y' または field_1002が'Y') かつ field_1003が'Y'であること」

---

## 実装ロジック

### Python実装例

```python
# app/services/validation_service.py
import json
import re
from datetime import datetime, date
from app.utils.db import get_db_connection
from app.models.admin.field_validation import FieldValidation

class ValidationService:
    """バリデーションサービス"""
    
    @staticmethod
    def validate_field(field_id, value):
        """フィールドのバリデーションを実行"""
        validations = FieldValidation.get_by_field(field_id)
        errors = []
        
        for validation in validations:
            is_valid, error = ValidationService._execute_rule(
                validation['rule_type'],
                value,
                validation['rule_parameter']
            )
            
            if not is_valid:
                errors.append(error or validation['error_message'])
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _execute_rule(rule_type, value, parameter):
        """ルールタイプに応じたバリデーションを実行"""
        validators = {
            'required': ValidationService._validate_required,
            'minlength': ValidationService._validate_minlength,
            'maxlength': ValidationService._validate_maxlength,
            'pattern': ValidationService._validate_pattern,
            'starts_with': ValidationService._validate_starts_with,
            'ends_with': ValidationService._validate_ends_with,
            'contains': ValidationService._validate_contains,
            'equals': ValidationService._validate_equals,
            'email': ValidationService._validate_email,
            'numeric': ValidationService._validate_numeric,
            'min_value': ValidationService._validate_min_value,
            'max_value': ValidationService._validate_max_value,
            'date_format': ValidationService._validate_date_format,
            'future_date': ValidationService._validate_future_date,
            'past_date': ValidationService._validate_past_date,
            'exists_in_table': ValidationService._validate_exists_in_table,
            'unique_in_table': ValidationService._validate_unique_in_table,
            'custom_query': ValidationService._validate_custom_query,
        }
        
        validator = validators.get(rule_type)
        if validator:
            return validator(value, parameter)
        return False, f"未知のバリデーションルール: {rule_type}"
    
    # --- 各バリデーションメソッド ---
    
    @staticmethod
    def _validate_required(value, parameter):
        """必須入力チェック"""
        if value is None or str(value).strip() == '':
            return False, None
        return True, None
    
    @staticmethod
    def _validate_minlength(value, parameter):
        """最小文字数チェック（パラメータ: "5"）"""
        if value is None:
            return True, None
        min_length = int(parameter)
        if len(str(value)) < min_length:
            return False, None
        return True, None
    
    @staticmethod
    def _validate_maxlength(value, parameter):
        """最大文字数チェック（パラメータ: "100"）"""
        if value is None:
            return True, None
        max_length = int(parameter)
        if len(str(value)) > max_length:
            return False, None
        return True, None
    
    @staticmethod
    def _validate_pattern(value, parameter):
        """正規表現パターンチェック（パラメータ: "^[A-Z][0-9]{5}$"）"""
        if value is None:
            return True, None
        if not re.match(parameter, str(value)):
            return False, None
        return True, None
    
    @staticmethod
    def _validate_starts_with(value, parameter):
        """前方一致チェック（パラメータ: "USER_"）"""
        if value is None:
            return True, None
        if not str(value).startswith(parameter):
            return False, None
        return True, None
    
    @staticmethod
    def _validate_ends_with(value, parameter):
        """後方一致チェック（パラメータ: "@example.com"）"""
        if value is None:
            return True, None
        if not str(value).endswith(parameter):
            return False, None
        return True, None
    
    @staticmethod
    def _validate_contains(value, parameter):
        """部分一致チェック（パラメータ: "test"）"""
        if value is None:
            return True, None
        if parameter not in str(value):
            return False, None
        return True, None
    
    @staticmethod
    def _validate_equals(value, parameter):
        """完全一致チェック（パラメータ: "APPROVED"）"""
        if value is None:
            return True, None
        if str(value) != parameter:
            return False, None
        return True, None
    
    @staticmethod
    def _validate_email(value, parameter):
        """メールアドレス形式チェック"""
        if value is None:
            return True, None
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, str(value)):
            return False, None
        return True, None
    
    @staticmethod
    def _validate_numeric(value, parameter):
        """数値形式チェック"""
        if value is None:
            return True, None
        try:
            float(str(value))
            return True, None
        except ValueError:
            return False, None
    
    @staticmethod
    def _validate_min_value(value, parameter):
        """最小値チェック（パラメータ: "0"）"""
        if value is None:
            return True, None
        min_val = float(parameter)
        try:
            if float(str(value)) < min_val:
                return False, None
            return True, None
        except ValueError:
            return False, "数値を入力してください"
    
    @staticmethod
    def _validate_max_value(value, parameter):
        """最大値チェック（パラメータ: "999999"）"""
        if value is None:
            return True, None
        max_val = float(parameter)
        try:
            if float(str(value)) > max_val:
                return False, None
            return True, None
        except ValueError:
            return False, "数値を入力してください"
    
    @staticmethod
    def _validate_date_format(value, parameter):
        """日付形式チェック（パラメータ: "YYYY-MM-DD"）"""
        if value is None:
            return True, None
        python_format = parameter.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d')
        try:
            datetime.strptime(str(value), python_format)
            return True, None
        except ValueError:
            return False, None
    
    @staticmethod
    def _validate_future_date(value, parameter):
        """未来日付チェック"""
        if value is None:
            return True, None
        try:
            input_date = datetime.strptime(str(value), '%Y-%m-%d').date()
            if input_date < date.today():
                return False, None
            return True, None
        except ValueError:
            return False, "日付形式が正しくありません"
    
    @staticmethod
    def _validate_past_date(value, parameter):
        """過去日付チェック"""
        if value is None:
            return True, None
        try:
            input_date = datetime.strptime(str(value), '%Y-%m-%d').date()
            if input_date > date.today():
                return False, None
            return True, None
        except ValueError:
            return False, "日付形式が正しくありません"
    
    @staticmethod
    def _validate_exists_in_table(value, parameter):
        """テーブル内存在チェック（パラメータ: JSON）"""
        if value is None:
            return True, None
        
        params = json.loads(parameter)
        table = params['table']
        column = params['column']
        condition = params.get('condition', '1=1')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = f"SELECT COUNT(*) FROM {table} WHERE {column} = :value AND {condition}"
        cursor.execute(sql, {'value': value})
        count = cursor.fetchone()[0]
        cursor.close()
        
        if count == 0:
            return False, None
        return True, None
    
    @staticmethod
    def _validate_unique_in_table(value, parameter):
        """テーブル内一意性チェック（パラメータ: JSON）"""
        if value is None:
            return True, None
        
        params = json.loads(parameter)
        table = params['table']
        column = params['column']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = f"SELECT COUNT(*) FROM {table} WHERE {column} = :value"
        cursor.execute(sql, {'value': value})
        count = cursor.fetchone()[0]
        cursor.close()
        
        if count > 0:
            return False, None
        return True, None
    
    @staticmethod
    def _validate_custom_query(value, parameter):
        """カスタムSQLクエリ（パラメータ: JSON）"""
        if value is None:
            return True, None
        
        params = json.loads(parameter)
        query = params['query']
        expect = params['expect']
        message = params.get('message')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(query, {'value': value})
        result = str(cursor.fetchone()[0])
        cursor.close()
        
        if result != expect:
            return False, message
        return True, None
```

---

## バリデーション実行順序

フィールドに複数のバリデーションルールが割り当てられている場合、`M_FIELD_VALIDATION.check_order`の昇順で実行されます。

### 推奨実行順序

1. **必須チェック** (`required`) - 最初に実行
2. **形式チェック** (`pattern`, `starts_with`, `email`, `numeric`等) - 軽量なチェック
3. **範囲チェック** (`minlength`, `maxlength`, `min_value`, `max_value`等)
4. **データベースチェック** (`exists_in_table`, `unique_in_table`, `custom_query`) - 最後に実行

---

## 実装時の注意事項

### 1. NULL値の扱い
- ほとんどのバリデーションルールは、値がNULLの場合は`True`を返します
- 必須チェックは`required`ルールで行うため、他のルールではNULLを許容します

### 2. パラメータの型変換
- 数値系のルール（`minlength`, `min_value`等）ではパラメータを`int()`または`float()`で変換
- 文字列系のルール（`pattern`, `starts_with`等）ではそのまま使用
- JSON系のルール（`exists_in_table`等）では`json.loads()`でパース

### 3. SQLインジェクション対策
- `exists_in_table`, `unique_in_table`, `custom_query`では**必ずバインド変数**（`:value`）を使用
- テーブル名・カラム名は信頼できるソース（マスターデータ）からのみ取得
- ユーザー入力をテーブル名・カラム名に使用しない

### 4. パフォーマンス
- データベースアクセスを伴うルールは実行順序を後ろに設定
- 軽量なチェック（`required`, `pattern`等）を先に実行して早期リターン

---

## 更新履歴

| 日付 | バージョン | 変更内容 |
|-----|----------|---------|
| 2026-05-22 | 2.0 | パラメータ設計を簡素化、新規ルールタイプ追加（starts_with, ends_with, contains, equals） |
| 2026-05-22 | 1.0 | 初版作成 |
