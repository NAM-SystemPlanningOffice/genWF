"""
バリデーションルール管理モデル
"""
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class ValidationRule:
    """バリデーションルール管理モデル"""

    @staticmethod
    def get_all():
        """
        全バリデーションルールを取得

        Returns:
            list: バリデーションルールのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                validation_rule_id,
                rule_code,
                rule_name,
                rule_type,
                rule_parameter,
                error_message,
                description,
                is_active
            FROM M_VALIDATION_RULE
            WHERE is_active = 'Y'
            ORDER BY rule_code
        """

        cursor.execute(sql)
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def get_by_id(validation_rule_id):
        """
        バリデーションルールIDからルールを取得

        Args:
            validation_rule_id: バリデーションルールID

        Returns:
            dict: バリデーションルール情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                validation_rule_id,
                rule_code,
                rule_name,
                rule_type,
                rule_parameter,
                error_message,
                description,
                is_active
            FROM M_VALIDATION_RULE
            WHERE validation_rule_id = :validation_rule_id
        """

        cursor.execute(sql, {'validation_rule_id': validation_rule_id})
        result = dict_fetchone(cursor)
        cursor.close()

        return result

    @staticmethod
    def get_by_code(rule_code):
        """
        ルールコードからルールを取得

        Args:
            rule_code: ルールコード

        Returns:
            dict: バリデーションルール情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                validation_rule_id,
                rule_code,
                rule_name,
                rule_type,
                rule_parameter,
                error_message,
                description,
                is_active
            FROM M_VALIDATION_RULE
            WHERE rule_code = :rule_code
        """

        cursor.execute(sql, {'rule_code': rule_code})
        result = dict_fetchone(cursor)
        cursor.close()

        return result

    @staticmethod
    def create(data):
        """
        バリデーションルールを新規作成

        Args:
            data: バリデーションルールデータ（dict）

        Returns:
            int: 作成されたバリデーションルールID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # シーケンスからIDを取得
        cursor.execute("SELECT SEQ_VALIDATION_RULE.NEXTVAL FROM DUAL")
        validation_rule_id = cursor.fetchone()[0]

        sql = """
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
                :validation_rule_id,
                :rule_code,
                :rule_name,
                :rule_type,
                :rule_parameter,
                :error_message,
                :description,
                :is_active
            )
        """

        params = {
            'validation_rule_id': validation_rule_id,
            'rule_code': data.get('rule_code'),
            'rule_name': data.get('rule_name'),
            'rule_type': data.get('rule_type'),
            'rule_parameter': data.get('rule_parameter'),
            'error_message': data.get('error_message'),
            'description': data.get('description'),
            'is_active': data.get('is_active', 'Y')
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return validation_rule_id

    @staticmethod
    def update(validation_rule_id, data):
        """
        バリデーションルールを更新

        Args:
            validation_rule_id: バリデーションルールID
            data: 更新データ（dict）

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_VALIDATION_RULE
            SET rule_code = :rule_code,
                rule_name = :rule_name,
                rule_type = :rule_type,
                rule_parameter = :rule_parameter,
                error_message = :error_message,
                description = :description,
                is_active = :is_active
            WHERE validation_rule_id = :validation_rule_id
        """

        params = {
            'validation_rule_id': validation_rule_id,
            'rule_code': data.get('rule_code'),
            'rule_name': data.get('rule_name'),
            'rule_type': data.get('rule_type'),
            'rule_parameter': data.get('rule_parameter'),
            'error_message': data.get('error_message'),
            'description': data.get('description'),
            'is_active': data.get('is_active', 'Y')
        }

        cursor.execute(sql, params)
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0

    @staticmethod
    def delete(validation_rule_id):
        """
        バリデーションルールを削除（論理削除）

        Args:
            validation_rule_id: バリデーションルールID

        Returns:
            bool: 削除成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_VALIDATION_RULE
            SET is_active = 'N'
            WHERE validation_rule_id = :validation_rule_id
        """

        cursor.execute(sql, {'validation_rule_id': validation_rule_id})
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0
