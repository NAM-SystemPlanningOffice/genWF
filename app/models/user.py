"""
ユーザー情報モデル
"""
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class User:
    """ユーザーモデル"""

    @staticmethod
    def get_by_id(user_id):
        """
        ユーザーIDからユーザー情報を取得

        Args:
            user_id: ユーザーID

        Returns:
            dict: ユーザー情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                user_cd as user_id,
                user_name,
                shozoku,
                shozoku_name
            FROM nam_user_admin.e_imdb2_users
            WHERE user_cd = :user_id
        """

        cursor.execute(sql, {'user_id': user_id})
        result = dict_fetchone(cursor)

        cursor.close()

        return result

    @staticmethod
    def get_approvers_by_shozoku(shozoku):
        """
        所属コードから承認者一覧を取得

        Args:
            shozoku: 所属コード

        Returns:
            list: 承認者リスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                user_cd as user_id,
                user_name
            FROM nam_user_admin.e_approver
            WHERE department_cd = :shozoku
            ORDER BY notes
        """

        cursor.execute(sql, {'shozoku': shozoku})
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def get_user_departments(user_id):
        """
        ユーザーの所属一覧を取得（本務・兼務）

        Args:
            user_id: ユーザーID

        Returns:
            list: 所属のリスト（本務が先頭）
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT DISTINCT
                shozoku,
                shozoku_name,
                department_main
            FROM nam_user_admin.e_imdb2_users
            WHERE user_cd = :user_id
              AND NOT (shozoku = '2310000' AND department_main = '0')
            ORDER BY department_main DESC
        """

        cursor.execute(sql, {'user_id': user_id})
        results = dict_factory(cursor)
        cursor.close()

        # shozokuが文字列'None'の場合はNoneに変換
        for dept in results:
            if dept.get('shozoku') == 'None':
                dept['shozoku'] = None

        return results

    @staticmethod
    def authenticate(user_id, password):
        """
        ユーザー認証

        Args:
            user_id: ユーザーID
            password: パスワード

        Returns:
            dict: 認証成功時はユーザー情報、失敗時はNone

        Note:
            実際の認証ロジックは環境に応じて実装してください
            （AD認証、LDAP認証等）
        """
        # TODO: 実際の認証ロジックを実装
        # ここではダミー実装
        user = User.get_by_id(user_id)
        if user:
            # パスワードチェック（ダミー）
            # 実際はAD認証等を使用
            return user

        return None

    @staticmethod
    def get_same_shozoku_users(user_id, shozoku):
        """
        同一所属のユーザー一覧を取得

        Args:
            user_id: 自分のユーザーID
            shozoku: 所属コード

        Returns:
            list: ユーザーリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                user_cd as user_id,
                user_name,
                shozoku
            FROM nam_user_admin.e_imdb2_users
            WHERE shozoku = :shozoku
              AND user_cd != :user_id
            ORDER BY user_name
        """

        cursor.execute(sql, {
            'shozoku': shozoku,
            'user_id': user_id
        })
        results = dict_factory(cursor)

        cursor.close()

        return results

    @staticmethod
    def get_approvers_by_resource_and_shozoku(table_name, resource_id, shozoku):
        """
        リソースIDと所属コードから承認者一覧を取得
        指定されたテーブル（またはView）から取得

        テーブルは必ず以下のカラムを持つ必要がある：
        - resource_id: リソースID
        - shozoku: 所属コード
        - approver: 承認者ユーザーID

        Args:
            table_name: 承認者テーブル名（例: nam_user_admin.boxex_approver）
            resource_id: リソースID
            shozoku: 申請者所属コード

        Returns:
            list: 承認者リスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # SQLインジェクション対策: テーブル名のバリデーション
        # スキーマ名.テーブル名 または テーブル名のみ許可
        if not table_name or not all(c.isalnum() or c in '._' for c in table_name):
            raise ValueError(f"無効なテーブル名: {table_name}")

        sql = f"""
            SELECT
                approver as user_id
            FROM {table_name}
            WHERE resource_id = :resource_id
              AND shozoku = :shozoku
            ORDER BY approver
        """

        cursor.execute(sql, {
            'resource_id': resource_id,
            'shozoku': shozoku
        })
        results = dict_factory(cursor)
        cursor.close()

        return results
