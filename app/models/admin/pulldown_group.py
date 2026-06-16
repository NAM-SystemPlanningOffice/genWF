"""
プルダウングループ管理モデル
"""
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class PulldownGroup:
    """プルダウングループ管理モデル"""

    @staticmethod
    def get_all():
        """
        全プルダウングループを取得

        Returns:
            list: プルダウングループのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                pulldown_group_id,
                group_code,
                group_name,
                description,
                is_dynamic,
                dynamic_query
            FROM M_PULLDOWN_GROUP
            ORDER BY group_code
        """

        cursor.execute(sql)
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def get_by_id(pulldown_group_id):
        """
        プルダウングループIDからグループを取得

        Args:
            pulldown_group_id: プルダウングループID

        Returns:
            dict: プルダウングループ情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                pulldown_group_id,
                group_code,
                group_name,
                description,
                is_dynamic,
                dynamic_query
            FROM M_PULLDOWN_GROUP
            WHERE pulldown_group_id = :pulldown_group_id
        """

        cursor.execute(sql, {'pulldown_group_id': pulldown_group_id})
        result = dict_fetchone(cursor)
        cursor.close()

        return result

    @staticmethod
    def create(data):
        """
        プルダウングループを新規作成

        Args:
            data: プルダウングループデータ（dict）

        Returns:
            int: 作成されたプルダウングループID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # シーケンスからIDを取得
        cursor.execute("SELECT SEQ_PULLDOWN_GROUP.NEXTVAL FROM DUAL")
        pulldown_group_id = cursor.fetchone()[0]

        sql = """
            INSERT INTO M_PULLDOWN_GROUP (
                pulldown_group_id,
                group_code,
                group_name,
                description,
                is_dynamic,
                dynamic_query
            ) VALUES (
                :pulldown_group_id,
                :group_code,
                :group_name,
                :description,
                :is_dynamic,
                :dynamic_query
            )
        """

        params = {
            'pulldown_group_id': pulldown_group_id,
            'group_code': data.get('group_code'),
            'group_name': data.get('group_name'),
            'description': data.get('description'),
            'is_dynamic': data.get('is_dynamic', 'N'),
            'dynamic_query': data.get('dynamic_query')
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return pulldown_group_id

    @staticmethod
    def update(pulldown_group_id, data):
        """
        プルダウングループを更新

        Args:
            pulldown_group_id: プルダウングループID
            data: 更新データ（dict）

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_PULLDOWN_GROUP
            SET group_code = :group_code,
                group_name = :group_name,
                description = :description,
                is_dynamic = :is_dynamic,
                dynamic_query = :dynamic_query
            WHERE pulldown_group_id = :pulldown_group_id
        """

        params = {
            'pulldown_group_id': pulldown_group_id,
            'group_code': data.get('group_code'),
            'group_name': data.get('group_name'),
            'description': data.get('description'),
            'is_dynamic': data.get('is_dynamic', 'N'),
            'dynamic_query': data.get('dynamic_query')
        }

        cursor.execute(sql, params)
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0

    @staticmethod
    def delete(pulldown_group_id):
        """
        プルダウングループを削除（物理削除）

        Args:
            pulldown_group_id: プルダウングループID

        Returns:
            bool: 削除成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            DELETE FROM M_PULLDOWN_GROUP
            WHERE pulldown_group_id = :pulldown_group_id
        """

        cursor.execute(sql, {'pulldown_group_id': pulldown_group_id})
        conn.commit()

        rows_deleted = cursor.rowcount
        cursor.close()

        return rows_deleted > 0
