"""
申請フィールド管理モデル
"""
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class ApplicationField:
    """申請フィールド管理モデル"""

    @staticmethod
    def get_by_application_type(application_type_id):
        """
        申請タイプIDからフィールド一覧を取得

        Args:
            application_type_id: 申請タイプID

        Returns:
            list: フィールドのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                field_id,
                application_type_id,
                field_code,
                field_name,
                field_type,
                is_required_create,
                is_required_modify,
                is_required_delete,
                is_editable_modify,
                is_visible,
                is_key_field,
                pulldown_group_id,
                resource_column_name,
                resource_label_column,
                display_order,
                default_value,
                placeholder,
                help_text,
                is_active
            FROM M_APPLICATION_FIELD
            WHERE application_type_id = :application_type_id
            ORDER BY
                CASE WHEN is_active = 'Y' THEN 0 ELSE 1 END,
                display_order,
                field_id
        """

        cursor.execute(sql, {'application_type_id': application_type_id})
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def get_by_id(field_id):
        """
        フィールドIDからフィールドを取得

        Args:
            field_id: フィールドID

        Returns:
            dict: フィールド情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                field_id,
                application_type_id,
                field_code,
                field_name,
                field_type,
                is_required_create,
                is_required_modify,
                is_required_delete,
                is_editable_modify,
                is_visible,
                is_key_field,
                pulldown_group_id,
                resource_column_name,
                resource_label_column,
                display_order,
                default_value,
                placeholder,
                help_text,
                is_active
            FROM M_APPLICATION_FIELD
            WHERE field_id = :field_id
        """

        cursor.execute(sql, {'field_id': field_id})
        result = dict_fetchone(cursor)
        cursor.close()

        return result

    @staticmethod
    def create(data):
        """
        フィールドを新規作成

        Args:
            data: フィールドデータ（dict）

        Returns:
            int: 作成されたフィールドID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # シーケンスからIDを取得
        cursor.execute("SELECT SEQ_APPLICATION_FIELD.NEXTVAL FROM DUAL")
        field_id = cursor.fetchone()[0]

        sql = """
            INSERT INTO M_APPLICATION_FIELD (
                field_id,
                application_type_id,
                field_code,
                field_name,
                field_type,
                is_required_create,
                is_required_modify,
                is_required_delete,
                is_editable_modify,
                is_visible,
                is_key_field,
                pulldown_group_id,
                resource_column_name,
                resource_label_column,
                display_order,
                default_value,
                placeholder,
                help_text
            ) VALUES (
                :field_id,
                :application_type_id,
                :field_code,
                :field_name,
                :field_type,
                :is_required_create,
                :is_required_modify,
                :is_required_delete,
                :is_editable_modify,
                :is_visible,
                :is_key_field,
                :pulldown_group_id,
                :resource_column_name,
                :resource_label_column,
                :display_order,
                :default_value,
                :placeholder,
                :help_text
            )
        """

        params = {
            'field_id': field_id,
            'application_type_id': data.get('application_type_id'),
            'field_code': data.get('field_code'),
            'field_name': data.get('field_name'),
            'field_type': data.get('field_type', 'text'),
            'is_required_create': data.get('is_required_create', 'N'),
            'is_required_modify': data.get('is_required_modify', 'N'),
            'is_required_delete': data.get('is_required_delete', 'N'),
            'is_editable_modify': data.get('is_editable_modify', 'Y'),
            'is_visible': data.get('is_visible', 'Y'),
            'is_key_field': data.get('is_key_field', 'N'),
            'pulldown_group_id': data.get('pulldown_group_id'),
            'resource_column_name': data.get('resource_column_name'),
            'resource_label_column': data.get('resource_label_column'),
            'display_order': data.get('display_order'),
            'default_value': data.get('default_value'),
            'placeholder': data.get('placeholder'),
            'help_text': data.get('help_text')
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return field_id

    @staticmethod
    def update(field_id, data):
        """
        フィールドを更新

        Args:
            field_id: フィールドID
            data: 更新データ（dict）

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_APPLICATION_FIELD
            SET field_code = :field_code,
                field_name = :field_name,
                field_type = :field_type,
                is_required_create = :is_required_create,
                is_required_modify = :is_required_modify,
                is_required_delete = :is_required_delete,
                is_editable_modify = :is_editable_modify,
                is_visible = :is_visible,
                is_key_field = :is_key_field,
                pulldown_group_id = :pulldown_group_id,
                resource_column_name = :resource_column_name,
                resource_label_column = :resource_label_column,
                display_order = :display_order,
                default_value = :default_value,
                placeholder = :placeholder,
                help_text = :help_text
            WHERE field_id = :field_id
        """

        params = {
            'field_id': field_id,
            'field_code': data.get('field_code'),
            'field_name': data.get('field_name'),
            'field_type': data.get('field_type', 'text'),
            'is_required_create': data.get('is_required_create', 'N'),
            'is_required_modify': data.get('is_required_modify', 'N'),
            'is_required_delete': data.get('is_required_delete', 'N'),
            'is_editable_modify': data.get('is_editable_modify', 'Y'),
            'is_visible': data.get('is_visible', 'Y'),
            'is_key_field': data.get('is_key_field', 'N'),
            'pulldown_group_id': data.get('pulldown_group_id'),
            'resource_column_name': data.get('resource_column_name'),
            'resource_label_column': data.get('resource_label_column'),
            'display_order': data.get('display_order'),
            'default_value': data.get('default_value'),
            'placeholder': data.get('placeholder'),
            'help_text': data.get('help_text')
        }

        cursor.execute(sql, params)
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0

    @staticmethod
    def delete(field_id):
        """
        フィールドを削除（論理削除：is_active='N'に更新）
        過去の申請データを保持するため物理削除しない

        Args:
            field_id: フィールドID

        Returns:
            bool: 削除成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_APPLICATION_FIELD
            SET is_active = 'N'
            WHERE field_id = :field_id
        """

        cursor.execute(sql, {'field_id': field_id})
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0
