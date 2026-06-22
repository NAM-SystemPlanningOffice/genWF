"""
管理者ユーザーモデル
"""
from app.utils.db import get_db_connection, dict_factory, dict_fetchone


class AdminUser:
    """管理者ユーザーモデル"""

    @staticmethod
    def is_admin(user_id):
        """
        ユーザーが管理者かどうかを判定（有効な管理者のみ）

        Args:
            user_id: ユーザーID

        Returns:
            bool: 管理者の場合True
        """
        from flask import current_app

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """
                SELECT user_id
                FROM M_ADMIN_USER
                WHERE user_id = :user_id
                AND is_active = 'Y'
            """

            current_app.logger.info(f'[is_admin] Checking user_id={user_id}')
            cursor.execute(sql, {'user_id': user_id})
            result = dict_fetchone(cursor)
            cursor.close()

            current_app.logger.info(f'[is_admin] Query result: {result}')
            return result is not None
        except Exception as e:
            current_app.logger.error(f'[is_admin] Error: {str(e)}')
            import traceback
            current_app.logger.error(traceback.format_exc())
            return False

    @staticmethod
    def get_all(include_inactive=False):
        """
        全管理者を取得

        Args:
            include_inactive: 無効な管理者も含めるか

        Returns:
            list: 管理者リスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                user_id,
                user_name,
                is_active,
                created_at,
                updated_at
            FROM M_ADMIN_USER
        """

        if not include_inactive:
            sql += " WHERE is_active = 'Y'"

        sql += " ORDER BY user_id"

        cursor.execute(sql)
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def get_by_id(user_id):
        """
        管理者をIDで取得

        Args:
            user_id: ユーザーID

        Returns:
            dict: 管理者情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                user_id,
                user_name,
                is_active,
                created_at,
                updated_at
            FROM M_ADMIN_USER
            WHERE user_id = :user_id
        """

        cursor.execute(sql, {'user_id': user_id})
        result = dict_fetchone(cursor)
        cursor.close()

        return result

    @staticmethod
    def create(data):
        """
        管理者を追加

        Args:
            data: 管理者データ

        Returns:
            str: user_id
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        from datetime import datetime

        sql = """
            INSERT INTO M_ADMIN_USER (
                user_id,
                user_name,
                is_active,
                created_at,
                updated_at
            ) VALUES (
                :user_id,
                :user_name,
                :is_active,
                :created_at,
                :updated_at
            )
        """

        params = {
            'user_id': data['user_id'],
            'user_name': data.get('user_name'),
            'is_active': data.get('is_active', 'Y'),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

        try:
            cursor.execute(sql, params)
            conn.commit()
            cursor.close()
            return data['user_id']
        except Exception as e:
            conn.rollback()
            cursor.close()
            raise e

    @staticmethod
    def update(user_id, data):
        """
        管理者を更新

        Args:
            user_id: ユーザーID
            data: 管理者データ

        Returns:
            bool: 成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        from datetime import datetime

        sql = """
            UPDATE M_ADMIN_USER
            SET
                user_name = :user_name,
                is_active = :is_active,
                updated_at = :updated_at
            WHERE user_id = :user_id
        """

        params = {
            'user_id': user_id,
            'user_name': data.get('user_name'),
            'is_active': data.get('is_active', 'Y'),
            'updated_at': datetime.now()
        }

        try:
            cursor.execute(sql, params)
            conn.commit()
            rows_updated = cursor.rowcount
            cursor.close()
            return rows_updated > 0
        except Exception as e:
            conn.rollback()
            cursor.close()
            raise e

    @staticmethod
    def add(user_id, user_name=None):
        """
        管理者を追加（後方互換性のため）

        Args:
            user_id: ユーザーID
            user_name: ユーザー名（任意）

        Returns:
            bool: 成功時True
        """
        data = {
            'user_id': user_id,
            'user_name': user_name,
            'is_active': 'Y'
        }
        return AdminUser.create(data) is not None

    @staticmethod
    def remove(user_id):
        """
        管理者を削除

        Args:
            user_id: ユーザーID

        Returns:
            bool: 成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            DELETE FROM M_ADMIN_USER
            WHERE user_id = :user_id
        """

        cursor.execute(sql, {'user_id': user_id})
        conn.commit()

        rows_deleted = cursor.rowcount
        cursor.close()

        return rows_deleted > 0
