"""
申請タイプ管理モデル
"""
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class ApplicationType:
    """申請タイプ管理モデル"""

    @staticmethod
    def get_all():
        """
        全申請タイプを取得

        Returns:
            list: 申請タイプのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                application_type_id,
                application_type_code,
                application_type_name,
                description,
                is_multi_record,
                record_add_mode,
                support_create,
                support_modify,
                support_delete,
                jurisdiction_restriction,
                workflow_definition_id,
                is_active
            FROM M_APPLICATION_TYPE
            ORDER BY application_type_code
        """

        cursor.execute(sql)
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def get_by_id(application_type_id):
        """
        申請タイプIDから申請タイプを取得

        Args:
            application_type_id: 申請タイプID

        Returns:
            dict: 申請タイプ情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                application_type_id,
                application_type_code,
                application_type_name,
                description,
                is_multi_record,
                record_add_mode,
                support_create,
                support_modify,
                support_delete,
                jurisdiction_restriction,
                allowed_shozoku_list,
                allowed_user_list,
                workflow_definition_id,
                resource_search_query,
                resource_detail_query,
                resource_member_query,
                resource_validation_query,
                resource_jurisdiction_column,
                is_under_development,
                is_active
            FROM M_APPLICATION_TYPE
            WHERE application_type_id = :application_type_id
        """

        cursor.execute(sql, {'application_type_id': application_type_id})
        result = dict_fetchone(cursor)
        cursor.close()

        return result

    @staticmethod
    def create(data):
        """
        申請タイプを新規作成

        Args:
            data: 申請タイプデータ（dict）

        Returns:
            int: 作成された申請タイプID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # シーケンスからIDを取得
        cursor.execute("SELECT SEQ_APPLICATION_TYPE.NEXTVAL FROM DUAL")
        application_type_id = cursor.fetchone()[0]

        sql = """
            INSERT INTO M_APPLICATION_TYPE (
                application_type_id,
                application_type_code,
                application_type_name,
                description,
                is_multi_record,
                record_add_mode,
                support_create,
                support_modify,
                support_delete,
                jurisdiction_restriction,
                allowed_shozoku_list,
                allowed_user_list,
                workflow_definition_id,
                resource_search_query,
                resource_detail_query,
                resource_member_query,
                resource_validation_query,
                resource_jurisdiction_column,
                is_under_development,
                is_active,
                created_at,
                updated_at
            ) VALUES (
                :application_type_id,
                :application_type_code,
                :application_type_name,
                :description,
                :is_multi_record,
                :record_add_mode,
                :support_create,
                :support_modify,
                :support_delete,
                :jurisdiction_restriction,
                :allowed_shozoku_list,
                :allowed_user_list,
                :workflow_definition_id,
                :resource_search_query,
                :resource_detail_query,
                :resource_member_query,
                :resource_validation_query,
                :resource_jurisdiction_column,
                :is_under_development,
                :is_active,
                SYSTIMESTAMP,
                SYSTIMESTAMP
            )
        """

        params = {
            'application_type_id': application_type_id,
            'application_type_code': data.get('application_type_code'),
            'application_type_name': data.get('application_type_name'),
            'description': data.get('description'),
            'is_multi_record': data.get('is_multi_record', 'N'),
            'record_add_mode': data.get('record_add_mode', 'select'),
            'support_create': data.get('support_create', 'N'),
            'support_modify': data.get('support_modify', 'N'),
            'support_delete': data.get('support_delete', 'N'),
            'jurisdiction_restriction': data.get('jurisdiction_restriction', 'any'),
            'allowed_shozoku_list': data.get('allowed_shozoku_list'),
            'allowed_user_list': data.get('allowed_user_list'),
            'workflow_definition_id': data.get('workflow_definition_id'),
            'resource_search_query': data.get('resource_search_query'),
            'resource_detail_query': data.get('resource_detail_query'),
            'resource_member_query': data.get('resource_member_query'),
            'resource_validation_query': data.get('resource_validation_query'),
            'resource_jurisdiction_column': data.get('resource_jurisdiction_column'),
            'is_under_development': data.get('is_under_development', 'N'),
            'is_active': data.get('is_active', 'Y')
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return application_type_id

    @staticmethod
    def update(application_type_id, data):
        """
        申請タイプを更新

        Args:
            application_type_id: 申請タイプID
            data: 更新データ（dict）

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_APPLICATION_TYPE
            SET application_type_code = :application_type_code,
                application_type_name = :application_type_name,
                description = :description,
                is_multi_record = :is_multi_record,
                record_add_mode = :record_add_mode,
                support_create = :support_create,
                support_modify = :support_modify,
                support_delete = :support_delete,
                jurisdiction_restriction = :jurisdiction_restriction,
                allowed_shozoku_list = :allowed_shozoku_list,
                allowed_user_list = :allowed_user_list,
                workflow_definition_id = :workflow_definition_id,
                resource_search_query = :resource_search_query,
                resource_detail_query = :resource_detail_query,
                resource_member_query = :resource_member_query,
                resource_validation_query = :resource_validation_query,
                resource_jurisdiction_column = :resource_jurisdiction_column,
                is_under_development = :is_under_development,
                is_active = :is_active,
                updated_at = SYSTIMESTAMP
            WHERE application_type_id = :application_type_id
        """

        params = {
            'application_type_id': application_type_id,
            'application_type_code': data.get('application_type_code'),
            'application_type_name': data.get('application_type_name'),
            'description': data.get('description'),
            'is_multi_record': data.get('is_multi_record', 'N'),
            'record_add_mode': data.get('record_add_mode', 'select'),
            'support_create': data.get('support_create', 'N'),
            'support_modify': data.get('support_modify', 'N'),
            'support_delete': data.get('support_delete', 'N'),
            'jurisdiction_restriction': data.get('jurisdiction_restriction', 'any'),
            'allowed_shozoku_list': data.get('allowed_shozoku_list'),
            'allowed_user_list': data.get('allowed_user_list'),
            'workflow_definition_id': data.get('workflow_definition_id'),
            'resource_search_query': data.get('resource_search_query'),
            'resource_detail_query': data.get('resource_detail_query'),
            'resource_member_query': data.get('resource_member_query'),
            'resource_validation_query': data.get('resource_validation_query'),
            'resource_jurisdiction_column': data.get('resource_jurisdiction_column'),
            'is_under_development': data.get('is_under_development', 'N'),
            'is_active': data.get('is_active', 'Y')
        }

        cursor.execute(sql, params)
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0

    @staticmethod
    def delete(application_type_id):
        """
        申請タイプを削除（論理削除）

        Args:
            application_type_id: 申請タイプID

        Returns:
            bool: 削除成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_APPLICATION_TYPE
            SET is_active = 'N'
            WHERE application_type_id = :application_type_id
        """

        cursor.execute(sql, {'application_type_id': application_type_id})
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0
