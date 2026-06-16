"""
バリデーションサービス
"""
import json
import re
from datetime import datetime, date
from app.utils.db import get_db_connection
from app.models.admin.field_validation import FieldValidation


class ValidationService:
    """バリデーションサービス"""

    @staticmethod
    def validate_field(field_id, value, operation_type='create', resource_id=None, all_field_values=None):
        """
        フィールドのバリデーションを実行

        Args:
            field_id: フィールドID
            value: 検証する値
            operation_type: 操作タイプ ('create' or 'modify')
            resource_id: リソースID（編集時、自分自身を除外するため）
            all_field_values: クロスフィールドバリデーション用の全フィールド値 dict {field_id: value}

        Returns:
            tuple: (is_valid, errors)
                is_valid: bool - すべてのバリデーションが成功したかどうか
                errors: list - エラーメッセージのリスト
        """
        validations = FieldValidation.get_by_field(field_id)
        errors = []

        for validation in validations:
            # 操作タイプに応じてルールを適用するか判定
            if operation_type == 'create' and validation.get('apply_on_create') != 'Y':
                continue
            if operation_type == 'modify' and validation.get('apply_on_modify') != 'Y':
                continue

            rule_type = validation['rule_type']

            # クロスフィールドバリデーションの場合
            if rule_type == 'cross_field':
                if all_field_values is None:
                    # クロスフィールドバリデーションは全フィールド値が必要
                    # 値が渡されていない場合はスキップ（サーバーサイドでのみ実行）
                    import logging
                    logging.warning(f'クロスフィールドバリデーション（field_id={field_id}）: all_field_valuesが未指定のためスキップ')
                    continue
                is_valid, error = ValidationService._validate_cross_field(
                    value,
                    validation['rule_parameter'],
                    all_field_values
                )
            else:
                is_valid, error = ValidationService._execute_rule(
                    validation['rule_type'],
                    value,
                    validation['rule_parameter'],
                    operation_type,
                    resource_id
                )

            if not is_valid:
                errors.append(error or validation['error_message'])

        return len(errors) == 0, errors

    @staticmethod
    def _execute_rule(rule_type, value, parameter, operation_type='create', resource_id=None):
        """
        ルールタイプに応じたバリデーションを実行

        Args:
            rule_type: ルールタイプ
            value: 検証する値
            parameter: ルールパラメータ
            operation_type: 操作タイプ
            resource_id: リソースID

        Returns:
            tuple: (is_valid, error_message)
        """
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
            # unique_in_table と custom_query は追加パラメータを渡す
            if rule_type == 'unique_in_table':
                return validator(value, parameter, operation_type, resource_id)
            elif rule_type == 'custom_query':
                return validator(value, parameter, resource_id)
            else:
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
        from flask import current_app
        value_str = str(value)
        result = value_str.endswith(parameter)
        current_app.logger.debug(f"[ends_with] value='{value_str}', parameter='{parameter}', endswith={result}")
        if not result:
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
    def _validate_unique_in_table(value, parameter, operation_type='create', resource_id=None):
        """
        テーブル内一意性チェック（パラメータ: JSON）

        Args:
            value: 検証する値
            parameter: JSONパラメータ {"table": "...", "column": "...", "key_column": "..."}
            operation_type: 操作タイプ（'create' or 'modify'）
            resource_id: リソースID（編集時、自分自身を除外）

        Returns:
            tuple: (is_valid, error_message)
        """
        if value is None or str(value).strip() == '':
            return True, None

        from flask import current_app
        params = json.loads(parameter)
        table = params['table']
        column = params['column']
        key_column = params.get('key_column', 'resource_id')  # デフォルトはresource_id

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = f"SELECT COUNT(*) FROM {table} WHERE {column} = :value"
        bind_params = {'value': value}

        # 編集時は自分自身を除外
        if operation_type == 'modify' and resource_id:
            sql += f" AND {key_column} != :resource_id"
            bind_params['resource_id'] = resource_id

        current_app.logger.debug(f"[unique_in_table] SQL: {sql}, params: {bind_params}")

        cursor.execute(sql, bind_params)
        count = cursor.fetchone()[0]
        cursor.close()

        current_app.logger.debug(f"[unique_in_table] count={count}, value='{value}'")

        if count > 0:
            return False, None
        return True, None

    @staticmethod
    def _validate_custom_query(value, parameter, resource_id=None):
        """
        カスタムSQLクエリ

        パラメータ: SQL クエリ（is_valid カラムを返す）
        クエリは 'Y' または 'N' を返す必要がある

        利用可能なプレースホルダー:
        - :field_value
        - :resource_id
        - :applicant_user_id
        - :applicant_shozoku
        """
        if value is None or value == '':
            return True, None

        # パラメータが空の場合はスキップ
        if not parameter or parameter.strip() == '':
            return True, None

        from flask import session
        import re

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # クエリ内で使われているプレースホルダーを抽出
            placeholders = set(re.findall(r':(\w+)', parameter))

            # パラメータを準備
            query_params = {}
            if 'field_value' in placeholders:
                query_params['field_value'] = value
            if 'resource_id' in placeholders:
                query_params['resource_id'] = resource_id
            if 'applicant_user_id' in placeholders:
                query_params['applicant_user_id'] = session.get('user_id')
            if 'applicant_shozoku' in placeholders:
                query_params['applicant_shozoku'] = session.get('shozoku')

            # SQLクエリを実行（is_validカラムを返すことを期待）
            cursor.execute(parameter, query_params)
            result = cursor.fetchone()
            cursor.close()

            if not result:
                return False, 'バリデーションクエリが結果を返しませんでした'

            # 最初のカラム（is_valid）を取得
            is_valid = str(result[0]).upper()

            if is_valid == 'Y':
                return True, None
            else:
                return False, None

        except Exception as e:
            cursor.close()
            return False, f'バリデーションエラー: {str(e)}'

    @staticmethod
    def _validate_cross_field(value, parameter, all_field_values):
        """
        クロスフィールドバリデーション（複数フィールド間の条件チェック）
        単一レコード申請のみ対応

        Args:
            value: 現在のフィールドの値
            parameter: JSON形式のパラメータ
                {
                    "condition": "value == 'Y' or ((field_1001 == 'Y' or field_1002 == 'Y') and field_1003 == 'Y')",
                    "fields": [1001, 1002, 1003]
                }
            all_field_values: 全フィールドの値（dict: {field_id: value}）

        Returns:
            tuple: (is_valid, error_message)
        """
        if value is None:
            value = ''

        try:
            params = json.loads(parameter)
            condition = params.get('condition', '')
            required_fields = params.get('fields', [])

            if not condition:
                return True, None

            # 必要なフィールドの値を取得
            field_vars = {'value': str(value)}
            for field_id in required_fields:
                field_value = all_field_values.get(int(field_id), '')
                field_vars[f'field_{field_id}'] = str(field_value) if field_value is not None else ''

            # 条件式を評価（安全な評価のため、__builtins__を空にする）
            result = eval(condition, {"__builtins__": {}}, field_vars)

            if result:
                return True, None
            else:
                return False, None

        except json.JSONDecodeError as e:
            return False, f'パラメータのJSON解析エラー: {str(e)}'
        except Exception as e:
            return False, f'条件式の評価エラー: {str(e)}'
