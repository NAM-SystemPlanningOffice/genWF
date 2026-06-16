"""
リソースモデル（既存設定の検索・取得）
"""
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class Resource:
    """リソースモデル"""

    @staticmethod
    def search_resources(search_query, search_params=None):
        """
        リソースを検索

        Args:
            search_query: 検索SQL（M_APPLICATION_TYPE.resource_search_query）
            search_params: 検索パラメータ（dict）

        Returns:
            list: リソースのリスト
        """
        if not search_query:
            return []

        conn = get_db_connection()
        cursor = conn.cursor()

        if search_params is None:
            search_params = {}

        # クエリ内に実際に存在するプレースホルダーだけをフィルタリング
        import re
        placeholders = set(re.findall(r':(\w+)', search_query))
        filtered_params = {k: v for k, v in search_params.items() if k in placeholders}

        try:
            cursor.execute(search_query, filtered_params)
            results = dict_factory(cursor)
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f'SQL実行エラー: {str(e)}')
            current_app.logger.error(f'Query: {search_query}')
            current_app.logger.error(f'Params: {filtered_params}')
            cursor.close()
            raise

        cursor.close()

        return results

    @staticmethod
    def get_resource_detail(detail_query, resource_id):
        """
        リソースの詳細を取得

        Args:
            detail_query: 詳細取得SQL（M_APPLICATION_TYPE.resource_detail_query）
            resource_id: リソースID

        Returns:
            dict: リソースの詳細情報
        """
        if not detail_query:
            return None

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(detail_query, {'resource_id': resource_id})
        result = dict_fetchone(cursor)

        cursor.close()

        return result

    @staticmethod
    def validate_resource(validation_query, validation_params):
        """
        リソースのバリデーション（重複チェック等）

        Args:
            validation_query: バリデーションSQL（M_APPLICATION_TYPE.resource_validation_query）
            validation_params: バリデーションパラメータ（dict）

        Returns:
            bool: バリデーション結果（True=OK, False=NG）
        """
        if not validation_query:
            return True

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(validation_query, validation_params)
        result = cursor.fetchone()

        cursor.close()

        # クエリの結果が0件ならOK、1件以上ならNG
        if result and len(result) > 0:
            count = result[0]
            return count == 0

        return True

    @staticmethod
    def get_gmail_groups(search_keyword=None):
        """
        Gmailグループを検索（T_RESOURCE_GMAIL_GROUPから取得）

        Args:
            search_keyword: 検索キーワード（email または name の部分一致）

        Returns:
            list: Gmailグループのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                group_email AS resource_id,
                group_email,
                group_name,
                owner_shozoku AS jurisdiction_shozoku,
                description,
                member_count,
                last_synced_at
            FROM T_RESOURCE_GMAIL_GROUP
            WHERE 1=1
        """

        params = {}

        if search_keyword:
            sql += """
                AND (
                    UPPER(group_email) LIKE UPPER(:keyword)
                    OR UPPER(group_name) LIKE UPPER(:keyword)
                )
            """
            params['keyword'] = f'%{search_keyword}%'

        sql += " ORDER BY group_email"

        cursor.execute(sql, params)
        results = dict_factory(cursor)

        cursor.close()

        return results

    @staticmethod
    def get_gmail_group_detail(group_email):
        """
        Gmailグループの詳細を取得

        Args:
            group_email: グループのメールアドレス

        Returns:
            dict: グループの詳細情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                group_email,
                group_name,
                owner_shozoku,
                description,
                member_count,
                is_external_allowed,
                last_synced_at,
                created_at,
                updated_at
            FROM T_RESOURCE_GMAIL_GROUP
            WHERE group_email = :group_email
        """

        cursor.execute(sql, {'group_email': group_email})
        result = dict_fetchone(cursor)

        cursor.close()

        return result
