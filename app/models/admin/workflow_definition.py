"""
ワークフロー定義管理モデル
"""
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class WorkflowDefinition:
    """ワークフロー定義管理モデル"""

    @staticmethod
    def get_all(include_inactive=False):
        """
        全ワークフロー定義を取得

        Args:
            include_inactive: 無効なものも含めるか

        Returns:
            list: ワークフロー定義のリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                workflow_definition_id,
                workflow_name,
                workflow_code,
                description,
                version,
                is_active,
                created_at,
                updated_at
            FROM M_WORKFLOW_DEFINITION
        """

        if not include_inactive:
            sql += " WHERE is_active = 'Y'"

        sql += " ORDER BY workflow_code, version DESC"

        cursor.execute(sql)
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def get_by_id(workflow_definition_id):
        """
        ワークフロー定義IDから定義を取得

        Args:
            workflow_definition_id: ワークフロー定義ID

        Returns:
            dict: ワークフロー定義情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                workflow_definition_id,
                workflow_name,
                workflow_code,
                description,
                version,
                is_active
            FROM M_WORKFLOW_DEFINITION
            WHERE workflow_definition_id = :workflow_definition_id
        """

        cursor.execute(sql, {'workflow_definition_id': workflow_definition_id})
        result = dict_fetchone(cursor)
        cursor.close()

        return result

    @staticmethod
    def get_nodes(workflow_definition_id):
        """
        ワークフロー定義のノード一覧を取得

        Args:
            workflow_definition_id: ワークフロー定義ID

        Returns:
            list: ノード定義のリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                node_definition_id,
                workflow_definition_id,
                node_seq,
                node_name,
                node_type,
                specific_value,
                skip_condition,
                is_report_only,
                approver_selection_required
            FROM M_WORKFLOW_NODE_DEFINITION
            WHERE workflow_definition_id = :workflow_definition_id
            ORDER BY node_seq
        """

        cursor.execute(sql, {'workflow_definition_id': workflow_definition_id})
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def create(data):
        """
        ワークフロー定義を新規作成

        Args:
            data: ワークフロー定義データ（dict）

        Returns:
            int: 作成されたワークフロー定義ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # シーケンスからIDを取得
        cursor.execute("SELECT SEQ_M_NODE_APPROVER.NEXTVAL FROM DUAL")
        workflow_definition_id = cursor.fetchone()[0]

        sql = """
            INSERT INTO M_WORKFLOW_DEFINITION (
                workflow_definition_id,
                workflow_name,
                workflow_code,
                description,
                is_active,
                version,
                created_at,
                updated_at
            ) VALUES (
                :workflow_definition_id,
                :workflow_name,
                :workflow_code,
                :description,
                :is_active,
                :version,
                SYSTIMESTAMP,
                SYSTIMESTAMP
            )
        """

        params = {
            'workflow_definition_id': workflow_definition_id,
            'workflow_name': data.get('workflow_name'),
            'workflow_code': data.get('workflow_code'),
            'description': data.get('description'),
            'is_active': data.get('is_active', 'Y'),
            'version': data.get('version', 1)
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return workflow_definition_id

    @staticmethod
    def update(workflow_definition_id, data):
        """
        ワークフロー定義を更新

        Args:
            workflow_definition_id: ワークフロー定義ID
            data: 更新データ（dict）

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_WORKFLOW_DEFINITION
            SET workflow_name = :workflow_name,
                workflow_code = :workflow_code,
                description = :description,
                is_active = :is_active,
                version = :version,
                updated_at = SYSTIMESTAMP
            WHERE workflow_definition_id = :workflow_definition_id
        """

        params = {
            'workflow_definition_id': workflow_definition_id,
            'workflow_name': data.get('workflow_name'),
            'workflow_code': data.get('workflow_code'),
            'description': data.get('description'),
            'is_active': data.get('is_active', 'Y'),
            'version': data.get('version', 1)
        }

        cursor.execute(sql, params)
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0

    @staticmethod
    def delete(workflow_definition_id):
        """
        ワークフロー定義を削除（論理削除）

        Args:
            workflow_definition_id: ワークフロー定義ID

        Returns:
            bool: 削除成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_WORKFLOW_DEFINITION
            SET is_active = 'N'
            WHERE workflow_definition_id = :workflow_definition_id
        """

        cursor.execute(sql, {'workflow_definition_id': workflow_definition_id})
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0
