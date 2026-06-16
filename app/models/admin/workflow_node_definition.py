"""
ワークフローノード定義管理モデル
"""
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class WorkflowNodeDefinition:
    """ワークフローノード定義管理モデル"""

    @staticmethod
    def get_by_id(node_definition_id):
        """
        ノード定義IDからノード定義を取得

        Args:
            node_definition_id: ノード定義ID

        Returns:
            dict: ノード定義情報
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
            WHERE node_definition_id = :node_definition_id
        """

        cursor.execute(sql, {'node_definition_id': node_definition_id})
        result = dict_fetchone(cursor)
        cursor.close()

        return result

    @staticmethod
    def create(data):
        """
        ノード定義を新規作成

        Args:
            data: ノード定義データ（dict）

        Returns:
            int: 作成されたノード定義ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # シーケンスからIDを取得
        cursor.execute("SELECT SEQ_WORKFLOW_NODE_DEF.NEXTVAL FROM DUAL")
        node_definition_id = cursor.fetchone()[0]

        sql = """
            INSERT INTO M_WORKFLOW_NODE_DEFINITION (
                node_definition_id,
                workflow_definition_id,
                node_seq,
                node_name,
                node_type,
                specific_value,
                skip_condition,
                is_report_only,
                approver_selection_required
            ) VALUES (
                :node_definition_id,
                :workflow_definition_id,
                :node_seq,
                :node_name,
                :node_type,
                :specific_value,
                :skip_condition,
                :is_report_only,
                :approver_selection_required
            )
        """

        params = {
            'node_definition_id': node_definition_id,
            'workflow_definition_id': data.get('workflow_definition_id'),
            'node_seq': data.get('node_seq'),
            'node_name': data.get('node_name'),
            'node_type': data.get('node_type'),
            'specific_value': data.get('specific_value'),
            'skip_condition': data.get('skip_condition'),
            'is_report_only': data.get('is_report_only', 'N'),
            'approver_selection_required': data.get('approver_selection_required', 'N')
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return node_definition_id

    @staticmethod
    def update(node_definition_id, data):
        """
        ノード定義を更新

        Args:
            node_definition_id: ノード定義ID
            data: 更新データ（dict）

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE M_WORKFLOW_NODE_DEFINITION
            SET node_seq = :node_seq,
                node_name = :node_name,
                node_type = :node_type,
                specific_value = :specific_value,
                skip_condition = :skip_condition,
                is_report_only = :is_report_only,
                approver_selection_required = :approver_selection_required
            WHERE node_definition_id = :node_definition_id
        """

        params = {
            'node_definition_id': node_definition_id,
            'node_seq': data.get('node_seq'),
            'node_name': data.get('node_name'),
            'node_type': data.get('node_type'),
            'specific_value': data.get('specific_value'),
            'skip_condition': data.get('skip_condition'),
            'is_report_only': data.get('is_report_only', 'N'),
            'approver_selection_required': data.get('approver_selection_required', 'N')
        }

        cursor.execute(sql, params)
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0

    @staticmethod
    def delete(node_definition_id):
        """
        ノード定義を削除（物理削除）

        Args:
            node_definition_id: ノード定義ID

        Returns:
            bool: 削除成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            DELETE FROM M_WORKFLOW_NODE_DEFINITION
            WHERE node_definition_id = :node_definition_id
        """

        cursor.execute(sql, {'node_definition_id': node_definition_id})
        conn.commit()

        rows_deleted = cursor.rowcount
        cursor.close()

        return rows_deleted > 0

    @staticmethod
    def get_auto_process_mappings(node_definition_id):
        """
        ノード定義に紐付く自動処理マッピングを取得

        Args:
            node_definition_id: ノード定義ID

        Returns:
            list: 自動処理マッピングのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                nap.node_definition_id,
                nap.auto_process_id,
                nap.process_order,
                nap.parameter_mapping_json,
                nap.retry_count,
                nap.timeout_seconds,
                nap.on_error,
                apd.process_code,
                apd.process_name,
                apd.process_type
            FROM M_WORKFLOW_NODE_AUTO_PROCESS nap
            INNER JOIN M_AUTO_PROCESS_DEFINITION apd
                ON nap.auto_process_id = apd.auto_process_id
            WHERE nap.node_definition_id = :node_definition_id
            ORDER BY nap.process_order
        """

        cursor.execute(sql, {'node_definition_id': node_definition_id})
        results = dict_factory(cursor)
        cursor.close()

        return results
