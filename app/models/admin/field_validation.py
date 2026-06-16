"""
フィールドバリデーション関連管理モデル
"""
from app.utils.db import get_db_connection, dict_factory


class FieldValidation:
    """フィールドバリデーション関連モデル"""

    @staticmethod
    def get_by_field(field_id):
        """
        フィールドIDからバリデーションルール一覧を取得

        Args:
            field_id: フィールドID

        Returns:
            list: バリデーションルールのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                fv.field_validation_id,
                fv.field_id,
                fv.validation_rule_id,
                fv.check_order,
                fv.apply_on_create,
                fv.apply_on_modify,
                fv.is_active,
                vr.rule_code,
                vr.rule_name,
                vr.rule_type,
                vr.rule_parameter,
                vr.error_message
            FROM M_FIELD_VALIDATION fv
            INNER JOIN M_VALIDATION_RULE vr
                ON fv.validation_rule_id = vr.validation_rule_id
            WHERE fv.field_id = :field_id
              AND fv.is_active = 'Y'
            ORDER BY fv.check_order
        """

        cursor.execute(sql, {'field_id': field_id})
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def add(field_id, validation_rule_id, check_order, apply_on_create='Y', apply_on_modify='Y'):
        """
        フィールドにバリデーションルールを追加

        Args:
            field_id: フィールドID
            validation_rule_id: バリデーションルールID
            check_order: チェック順序
            apply_on_create: 新規作成時に適用するか（デフォルト: Y）
            apply_on_modify: 編集時に適用するか（デフォルト: Y）

        Returns:
            int: 作成されたフィールドバリデーションID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # シーケンスからIDを取得
        cursor.execute("SELECT SEQ_FIELD_VALIDATION.NEXTVAL FROM DUAL")
        field_validation_id = cursor.fetchone()[0]

        sql = """
            INSERT INTO M_FIELD_VALIDATION (
                field_validation_id,
                field_id,
                validation_rule_id,
                check_order,
                apply_on_create,
                apply_on_modify,
                is_active
            ) VALUES (
                :field_validation_id,
                :field_id,
                :validation_rule_id,
                :check_order,
                :apply_on_create,
                :apply_on_modify,
                'Y'
            )
        """

        params = {
            'field_validation_id': field_validation_id,
            'field_id': field_id,
            'validation_rule_id': validation_rule_id,
            'check_order': check_order,
            'apply_on_create': apply_on_create,
            'apply_on_modify': apply_on_modify
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return field_validation_id

    @staticmethod
    def remove(field_validation_id):
        """
        フィールドからバリデーションルールを削除

        Args:
            field_validation_id: フィールドバリデーションID

        Returns:
            bool: 削除成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            DELETE FROM M_FIELD_VALIDATION
            WHERE field_validation_id = :field_validation_id
        """

        cursor.execute(sql, {'field_validation_id': field_validation_id})
        conn.commit()

        rows_deleted = cursor.rowcount
        cursor.close()

        return rows_deleted > 0

    @staticmethod
    def update_order(field_validation_id, check_order):
        """
        チェック順序を更新

        Args:
            field_validation_id: フィールドバリデーションID
            check_order: 新しいチェック順序

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_FIELD_VALIDATION
            SET check_order = :check_order
            WHERE field_validation_id = :field_validation_id
        """

        cursor.execute(sql, {
            'check_order': check_order,
            'field_validation_id': field_validation_id
        })
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0
