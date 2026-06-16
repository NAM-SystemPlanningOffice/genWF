"""
ワークフローモデル
"""
from datetime import datetime
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class WorkflowDefinition:
    """ワークフロー定義モデル"""

    @staticmethod
    def get_by_id(workflow_definition_id):
        """
        ワークフロー定義IDからワークフロー定義を取得

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
                is_active,
                version
            FROM M_WORKFLOW_DEFINITION
            WHERE workflow_definition_id = :workflow_definition_id
              AND is_active = 'Y'
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


class WorkflowInstance:
    """ワークフローインスタンスモデル"""

    @staticmethod
    def create(application_id, workflow_definition_id):
        """
        ワークフローインスタンスを作成

        Args:
            application_id: 申請ID
            workflow_definition_id: ワークフロー定義ID

        Returns:
            int: 作成されたワークフローインスタンスID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # シーケンスからワークフローインスタンスIDを取得
        cursor.execute("SELECT SEQ_WORKFLOW_INSTANCE.NEXTVAL FROM DUAL")
        workflow_instance_id = cursor.fetchone()[0]

        now = datetime.now()

        sql = """
            INSERT INTO T_WORKFLOW_INSTANCE (
                workflow_instance_id,
                application_id,
                workflow_definition_id,
                current_node_seq,
                workflow_status,
                started_at
            ) VALUES (
                :workflow_instance_id,
                :application_id,
                :workflow_definition_id,
                1,
                'in_progress',
                :started_at
            )
        """

        params = {
            'workflow_instance_id': workflow_instance_id,
            'application_id': application_id,
            'workflow_definition_id': workflow_definition_id,
            'started_at': now
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return workflow_instance_id

    @staticmethod
    def get_by_application(application_id):
        """
        申請IDから最新のワークフローインスタンスを取得

        Args:
            application_id: 申請ID

        Returns:
            dict: ワークフローインスタンス情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                workflow_instance_id,
                application_id,
                workflow_definition_id,
                current_node_seq,
                workflow_status,
                started_at,
                completed_at
            FROM T_WORKFLOW_INSTANCE
            WHERE application_id = :application_id
            ORDER BY started_at DESC
            FETCH FIRST 1 ROWS ONLY
        """

        cursor.execute(sql, {'application_id': application_id})
        result = dict_fetchone(cursor)

        cursor.close()

        return result

    @staticmethod
    def update_current_node(workflow_instance_id, node_seq):
        """
        現在のノード順序を更新

        Args:
            workflow_instance_id: ワークフローインスタンスID
            node_seq: ノード順序番号

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE T_WORKFLOW_INSTANCE
            SET current_node_seq = :node_seq
            WHERE workflow_instance_id = :workflow_instance_id
        """

        cursor.execute(sql, {
            'node_seq': node_seq,
            'workflow_instance_id': workflow_instance_id
        })
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0

    @staticmethod
    def complete(workflow_instance_id, status):
        """
        ワークフローを完了

        Args:
            workflow_instance_id: ワークフローインスタンスID
            status: 完了ステータス（completed/rejected）

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        now = datetime.now()

        sql = """
            UPDATE T_WORKFLOW_INSTANCE
            SET workflow_status = :status,
                completed_at = :completed_at
            WHERE workflow_instance_id = :workflow_instance_id
        """

        cursor.execute(sql, {
            'status': status,
            'completed_at': now,
            'workflow_instance_id': workflow_instance_id
        })
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0

    @staticmethod
    def withdraw(workflow_instance_id):
        """
        ワークフローを取り下げ（申請者による取り下げ）

        Args:
            workflow_instance_id: ワークフローインスタンスID

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        now = datetime.now()

        # ワークフローインスタンスを withdrawn に更新
        sql_wf = """
            UPDATE T_WORKFLOW_INSTANCE
            SET workflow_status = 'withdrawn',
                completed_at = :completed_at
            WHERE workflow_instance_id = :workflow_instance_id
        """

        cursor.execute(sql_wf, {
            'completed_at': now,
            'workflow_instance_id': workflow_instance_id
        })

        # 現在 pending のノードを withdrawn に更新
        sql_node = """
            UPDATE T_WORKFLOW_NODE_INSTANCE
            SET node_status = 'withdrawn',
                actioned_at = :actioned_at
            WHERE workflow_instance_id = :workflow_instance_id
              AND node_status = 'pending'
        """

        cursor.execute(sql_node, {
            'actioned_at': now,
            'workflow_instance_id': workflow_instance_id
        })

        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0


class WorkflowNodeInstance:
    """ワークフローノードインスタンスモデル"""

    @staticmethod
    def create(workflow_instance_id, node_definition_id, node_seq):
        """
        ワークフローノードインスタンスを作成

        Args:
            workflow_instance_id: ワークフローインスタンスID
            node_definition_id: ノード定義ID
            node_seq: ノード順序番号

        Returns:
            int: 作成されたノードインスタンスID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # シーケンスからノードインスタンスIDを取得
        cursor.execute("SELECT SEQ_WORKFLOW_NODE_INST.NEXTVAL FROM DUAL")
        node_instance_id = cursor.fetchone()[0]

        # 最初のノードは即座にpending、それ以外はwaiting
        node_status = 'pending' if node_seq == 1 else 'waiting'
        arrived_at = datetime.now() if node_seq == 1 else None

        sql = """
            INSERT INTO T_WORKFLOW_NODE_INSTANCE (
                node_instance_id,
                workflow_instance_id,
                node_definition_id,
                node_seq,
                node_status,
                arrived_at
            ) VALUES (
                :node_instance_id,
                :workflow_instance_id,
                :node_definition_id,
                :node_seq,
                :node_status,
                :arrived_at
            )
        """

        params = {
            'node_instance_id': node_instance_id,
            'workflow_instance_id': workflow_instance_id,
            'node_definition_id': node_definition_id,
            'node_seq': node_seq,
            'node_status': node_status,
            'arrived_at': arrived_at
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return node_instance_id

    @staticmethod
    def get_by_workflow(workflow_instance_id):
        """
        ワークフローインスタンスIDからノードインスタンス一覧を取得

        Args:
            workflow_instance_id: ワークフローインスタンスID

        Returns:
            list: ノードインスタンスのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                ni.node_instance_id,
                ni.workflow_instance_id,
                ni.node_definition_id,
                ni.node_seq,
                ni.node_status,
                ni.assigned_user_id,
                ni.arrived_at,
                ni.assigned_at,
                ni.actioned_at,
                ni.action_comment,
                nd.node_name,
                nd.node_type,
                nd.is_report_only
            FROM T_WORKFLOW_NODE_INSTANCE ni
            INNER JOIN M_WORKFLOW_NODE_DEFINITION nd
                ON ni.node_definition_id = nd.node_definition_id
            WHERE ni.workflow_instance_id = :workflow_instance_id
            ORDER BY ni.node_seq
        """

        cursor.execute(sql, {'workflow_instance_id': workflow_instance_id})
        results = dict_factory(cursor)

        cursor.close()

        return results

    @staticmethod
    def update_status(node_instance_id, status, assigned_user_id=None, comment=None):
        """
        ノードインスタンスのステータスを更新

        Args:
            node_instance_id: ノードインスタンスID
            status: 新しいステータス
            assigned_user_id: 処理者のユーザーID（任意）
            comment: 処理コメント（任意）

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        now = datetime.now()

        sql = """
            UPDATE T_WORKFLOW_NODE_INSTANCE
            SET node_status = :status,
                assigned_user_id = :assigned_user_id,
                actioned_at = :actioned_at,
                action_comment = :action_comment
            WHERE node_instance_id = :node_instance_id
        """

        cursor.execute(sql, {
            'status': status,
            'assigned_user_id': assigned_user_id,
            'actioned_at': now,
            'action_comment': comment,
            'node_instance_id': node_instance_id
        })
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0
