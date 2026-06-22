"""
ノード承認者マスタモデル
"""
from app.utils.db import get_db_connection, dict_factory, dict_fetchone


class NodeApprover:
    """ノード承認者マスタモデル"""

    @staticmethod
    def get_all(include_inactive=False):
        """
        全てのノード承認者を取得

        Args:
            include_inactive: 無効なレコードも含めるか

        Returns:
            list: ノード承認者リスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                node_approver_id,
                specific_node,
                approver_user_id,
                approver_order,
                is_active
            FROM M_NODE_APPROVER
        """

        if not include_inactive:
            sql += " WHERE is_active = 'Y'"

        sql += " ORDER BY specific_node, approver_order, approver_user_id"

        cursor.execute(sql)
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def get_by_id(node_approver_id):
        """
        IDでノード承認者を取得

        Args:
            node_approver_id: ノード承認者ID

        Returns:
            dict: ノード承認者情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                node_approver_id,
                specific_node,
                approver_user_id,
                approver_order,
                is_active
            FROM M_NODE_APPROVER
            WHERE node_approver_id = :node_approver_id
        """

        cursor.execute(sql, {'node_approver_id': node_approver_id})
        result = dict_fetchone(cursor)
        cursor.close()

        return result

    @staticmethod
    def get_by_specific_node(specific_node, include_inactive=False):
        """
        特定ノードの承認者を取得

        Args:
            specific_node: 特定ノード識別子
            include_inactive: 無効なレコードも含めるか

        Returns:
            list: ノード承認者リスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                node_approver_id,
                specific_node,
                approver_user_id,
                approver_order,
                is_active
            FROM M_NODE_APPROVER
            WHERE specific_node = :specific_node
        """

        if not include_inactive:
            sql += " AND is_active = 'Y'"

        sql += " ORDER BY approver_order, approver_user_id"

        cursor.execute(sql, {'specific_node': specific_node})
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def create(data):
        """
        ノード承認者を追加

        Args:
            data: ノード承認者データ

        Returns:
            int: node_approver_id
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO M_NODE_APPROVER (
                node_approver_id,
                specific_node,
                approver_user_id,
                approver_order,
                is_active
            ) VALUES (
                SEQ_M_NODE_APPROVER.NEXTVAL,
                :specific_node,
                :approver_user_id,
                :approver_order,
                :is_active
            )
            RETURNING node_approver_id INTO :new_id
        """

        params = {
            'specific_node': data['specific_node'],
            'approver_user_id': data['approver_user_id'],
            'approver_order': data.get('approver_order'),
            'is_active': data.get('is_active', 'Y')
        }

        try:
            new_id_var = cursor.var(int)
            params['new_id'] = new_id_var
            cursor.execute(sql, params)
            conn.commit()
            new_id = new_id_var.getvalue()[0]
            cursor.close()
            return new_id
        except Exception as e:
            conn.rollback()
            cursor.close()
            raise e

    @staticmethod
    def update(node_approver_id, data):
        """
        ノード承認者を更新

        Args:
            node_approver_id: ノード承認者ID
            data: ノード承認者データ

        Returns:
            bool: 成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_NODE_APPROVER
            SET
                specific_node = :specific_node,
                approver_user_id = :approver_user_id,
                approver_order = :approver_order,
                is_active = :is_active
            WHERE node_approver_id = :node_approver_id
        """

        params = {
            'node_approver_id': node_approver_id,
            'specific_node': data['specific_node'],
            'approver_user_id': data['approver_user_id'],
            'approver_order': data.get('approver_order'),
            'is_active': data.get('is_active', 'Y')
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
    def delete(node_approver_id):
        """
        ノード承認者を削除（論理削除）

        Args:
            node_approver_id: ノード承認者ID

        Returns:
            bool: 成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_NODE_APPROVER
            SET is_active = 'N'
            WHERE node_approver_id = :node_approver_id
        """

        try:
            cursor.execute(sql, {'node_approver_id': node_approver_id})
            conn.commit()
            rows_updated = cursor.rowcount
            cursor.close()
            return rows_updated > 0
        except Exception as e:
            conn.rollback()
            cursor.close()
            raise e
