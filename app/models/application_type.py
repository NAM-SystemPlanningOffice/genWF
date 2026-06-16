"""
申請種類マスタモデル
"""
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class ApplicationType:
    """申請種類モデル"""

    @staticmethod
    def get_all_active(include_under_development=False, applicant_shozoku=None, applicant_user_id=None):
        """
        有効な申請種類一覧を取得

        Args:
            include_under_development: 開発中のものも含めるか（デフォルト: False）
            applicant_shozoku: 申請者の所属コード（所属制限フィルタリング用、省略時は全件）

        Returns:
            list: 申請種類のリスト（申請可能な申請種類のみ）
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause = "WHERE is_active = 'Y'"
        if not include_under_development:
            where_clause += " AND (is_under_development = 'N' OR is_under_development IS NULL)"

        sql = f"""
            SELECT
                application_type_id,
                application_type_code,
                application_type_name,
                description,
                workflow_definition_id,
                is_multi_record,
                record_add_mode,
                jurisdiction_restriction,
                allowed_shozoku_list,
                allowed_user_list,
                support_create,
                support_modify,
                support_delete,
                resource_search_query,
                resource_detail_query,
                resource_member_query,
                resource_validation_query,
                resource_jurisdiction_column,
                is_under_development,
                display_order
            FROM M_APPLICATION_TYPE
            {where_clause}
            ORDER BY display_order, application_type_id
        """

        cursor.execute(sql)
        results = dict_factory(cursor)

        cursor.close()

        # 申請者の所属・ユーザーIDによる絞り込み
        if applicant_shozoku or applicant_user_id:
            filtered_results = []
            for app_type in results:
                if ApplicationType.is_allowed_to_apply(app_type, applicant_shozoku, applicant_user_id):
                    filtered_results.append(app_type)
            return filtered_results

        return results

    @staticmethod
    def get_by_id(application_type_id):
        """
        申請種類IDから申請種類を取得

        Args:
            application_type_id: 申請種類ID

        Returns:
            dict: 申請種類情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                application_type_id,
                application_type_code,
                application_type_name,
                description,
                workflow_definition_id,
                is_multi_record,
                record_add_mode,
                jurisdiction_restriction,
                allowed_shozoku_list,
                allowed_user_list,
                support_create,
                support_modify,
                support_delete,
                resource_search_query,
                resource_detail_query,
                resource_member_query,
                resource_validation_query,
                resource_jurisdiction_column,
                is_under_development
            FROM M_APPLICATION_TYPE
            WHERE application_type_id = :application_type_id
              AND is_active = 'Y'
        """

        cursor.execute(sql, {'application_type_id': application_type_id})
        result = dict_fetchone(cursor)

        cursor.close()

        # CLOBオブジェクトを文字列に変換
        if result:
            for key in ['resource_search_query', 'resource_detail_query', 'resource_member_query', 'resource_validation_query']:
                if key in result and result[key] and hasattr(result[key], 'read'):
                    result[key] = result[key].read()

        return result

    @staticmethod
    def check_can_apply(application_type_id, user_shozoku, jurisdiction_shozoku=None):
        """
        申請可能かをチェック

        Args:
            application_type_id: 申請種類ID
            user_shozoku: 申請者の所属コード
            jurisdiction_shozoku: 所管所属コード（任意）

        Returns:
            bool: 申請可能な場合True
        """
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type:
            return False

        restriction = app_type.get('jurisdiction_restriction')

        # 制限なし
        if restriction == 'any':
            return True

        # 所管所属のみ
        if restriction == 'jurisdiction_only':
            if jurisdiction_shozoku:
                return user_shozoku == jurisdiction_shozoku
            return False

        # 特定所属リスト
        if restriction == 'specific':
            allowed_list = app_type.get('allowed_shozoku_list', '')
            if allowed_list:
                allowed = [s.strip() for s in allowed_list.split(',')]
                return user_shozoku in allowed
            return False

        return True

    @staticmethod
    def is_allowed_to_apply(app_type, applicant_shozoku=None, applicant_user_id=None):
        """
        申請タイプが指定されたユーザー・所属から申請可能かをチェック

        Args:
            app_type: 申請種類オブジェクト（辞書）
            applicant_shozoku: 申請者の所属コード（任意）
            applicant_user_id: 申請者のユーザーID（任意）

        Returns:
            bool: 申請可能な場合True
        """
        restriction = app_type.get('jurisdiction_restriction')

        # 制限なし
        if not restriction or restriction == 'any':
            return True

        # 特定所属のみ
        if restriction == 'specific':
            if not applicant_shozoku:
                return False
            allowed_list = app_type.get('allowed_shozoku_list', '')
            if allowed_list:
                allowed = [s.strip() for s in allowed_list.split(',')]
                return applicant_shozoku in allowed
            return False

        # 特定ユーザーのみ
        if restriction == 'specific_user':
            if not applicant_user_id:
                return False
            allowed_list = app_type.get('allowed_user_list', '')
            if allowed_list:
                allowed = [s.strip() for s in allowed_list.split(',')]
                return applicant_user_id in allowed
            return False

        # その他は制限なし扱い
        return True

    @staticmethod
    def is_allowed_shozoku(app_type, applicant_shozoku):
        """
        旧メソッド - 互換性のため残す
        is_allowed_to_apply() を使用してください
        """
        return ApplicationType.is_allowed_to_apply(app_type, applicant_shozoku, None)
