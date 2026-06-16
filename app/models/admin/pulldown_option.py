"""
プルダウン選択肢管理モデル
"""
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class PulldownOption:
    """プルダウン選択肢管理モデル"""

    @staticmethod
    def get_by_group(pulldown_group_id):
        """
        プルダウングループIDから選択肢一覧を取得

        Args:
            pulldown_group_id: プルダウングループID

        Returns:
            list: 選択肢のリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                option_id,
                pulldown_group_id,
                option_value,
                option_label,
                display_order,
                is_active,
                parent_option_id
            FROM M_PULLDOWN_OPTION
            WHERE pulldown_group_id = :pulldown_group_id
            ORDER BY display_order, option_id
        """

        cursor.execute(sql, {'pulldown_group_id': pulldown_group_id})
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def get_by_id(option_id):
        """
        選択肢IDから選択肢を取得

        Args:
            option_id: 選択肢ID

        Returns:
            dict: 選択肢情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                option_id,
                pulldown_group_id,
                option_value,
                option_label,
                display_order,
                is_active,
                parent_option_id
            FROM M_PULLDOWN_OPTION
            WHERE option_id = :option_id
        """

        cursor.execute(sql, {'option_id': option_id})
        result = dict_fetchone(cursor)
        cursor.close()

        return result

    @staticmethod
    def create(data):
        """
        選択肢を新規作成

        Args:
            data: 選択肢データ（dict）

        Returns:
            int: 作成された選択肢ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # シーケンスからIDを取得
        cursor.execute("SELECT SEQ_PULLDOWN_OPTION.NEXTVAL FROM DUAL")
        option_id = cursor.fetchone()[0]

        sql = """
            INSERT INTO M_PULLDOWN_OPTION (
                option_id,
                pulldown_group_id,
                option_value,
                option_label,
                display_order,
                is_active,
                parent_option_id
            ) VALUES (
                :option_id,
                :pulldown_group_id,
                :option_value,
                :option_label,
                :display_order,
                :is_active,
                :parent_option_id
            )
        """

        params = {
            'option_id': option_id,
            'pulldown_group_id': data.get('pulldown_group_id'),
            'option_value': data.get('option_value'),
            'option_label': data.get('option_label'),
            'display_order': data.get('display_order'),
            'is_active': data.get('is_active', 'Y'),
            'parent_option_id': data.get('parent_option_id')
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return option_id

    @staticmethod
    def update(option_id, data):
        """
        選択肢を更新

        Args:
            option_id: 選択肢ID
            data: 更新データ（dict）

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_PULLDOWN_OPTION
            SET option_value = :option_value,
                option_label = :option_label,
                display_order = :display_order,
                is_active = :is_active,
                parent_option_id = :parent_option_id
            WHERE option_id = :option_id
        """

        params = {
            'option_id': option_id,
            'option_value': data.get('option_value'),
            'option_label': data.get('option_label'),
            'display_order': data.get('display_order'),
            'is_active': data.get('is_active', 'Y'),
            'parent_option_id': data.get('parent_option_id')
        }

        cursor.execute(sql, params)
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0

    @staticmethod
    def delete(option_id):
        """
        選択肢を削除（物理削除）

        Args:
            option_id: 選択肢ID

        Returns:
            bool: 削除成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            DELETE FROM M_PULLDOWN_OPTION
            WHERE option_id = :option_id
        """

        cursor.execute(sql, {'option_id': option_id})
        conn.commit()

        rows_deleted = cursor.rowcount
        cursor.close()

        return rows_deleted > 0
