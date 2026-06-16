"""
承認タスクモデル
"""
from app.utils.db import get_db_connection, dict_factory


class ApprovalTask:
    """承認タスクモデル"""

    @staticmethod
    def get_pending_tasks(approver_user_id):
        """
        承認者のユーザーIDから承認待ちタスク一覧を取得

        Args:
            approver_user_id: 承認者のユーザーID

        Returns:
            list: 承認待ちタスクのリスト
        """
        from flask import current_app
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                a.application_id,
                a.application_type_id,
                a.action_type,
                a.applicant_user_id,
                a.applicant_shozoku,
                a.application_title,
                a.application_status,
                a.submitted_at,
                t.application_type_name,
                ni.node_instance_id,
                ni.node_seq,
                ni.arrived_at,
                nd.node_name,
                nd.node_type,
                wi.workflow_instance_id,
                na.approval_status
            FROM T_APPLICATION a
            INNER JOIN M_APPLICATION_TYPE t
                ON a.application_type_id = t.application_type_id
            INNER JOIN T_WORKFLOW_INSTANCE wi
                ON a.application_id = wi.application_id
            INNER JOIN T_WORKFLOW_NODE_INSTANCE ni
                ON wi.workflow_instance_id = ni.workflow_instance_id
            INNER JOIN M_WORKFLOW_NODE_DEFINITION nd
                ON ni.node_definition_id = nd.node_definition_id
            INNER JOIN T_WORKFLOW_NODE_APPROVER na
                ON ni.node_instance_id = na.node_instance_id
            WHERE na.approver_user_id = :approver_user_id
              AND ni.node_status = 'pending'
              AND a.application_status = 'submitted'
              AND na.approval_status = 'pending'
            ORDER BY a.submitted_at ASC
        """

        cursor.execute(sql, {'approver_user_id': approver_user_id})
        results = dict_factory(cursor)

        current_app.logger.info(f'[get_pending_tasks] user={approver_user_id}, count={len(results)}')
        if results:
            current_app.logger.info(f'[get_pending_tasks] 最初のタスク: app_id={results[0]["application_id"]}, node_id={results[0]["node_instance_id"]}, status={results[0].get("approval_status")}')

        cursor.close()

        return results

    @staticmethod
    def get_task_detail(node_instance_id, approver_user_id):
        """
        承認タスクの詳細を取得（承認者チェック付き）

        Args:
            node_instance_id: ノードインスタンスID
            approver_user_id: 承認者のユーザーID

        Returns:
            dict: タスクの詳細情報（承認権限がない場合はNone）
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                a.application_id,
                a.application_type_id,
                a.action_type,
                a.applicant_user_id,
                a.applicant_shozoku,
                a.jurisdiction_shozoku,
                a.application_title,
                a.application_status,
                a.reference_resource_id,
                a.remarks,
                a.submitted_at,
                t.application_type_name,
                ni.node_instance_id,
                ni.node_seq,
                ni.node_status,
                ni.arrived_at,
                nd.node_name,
                nd.node_type,
                nd.is_report_only,
                wi.workflow_instance_id,
                wi.workflow_definition_id
            FROM T_WORKFLOW_NODE_INSTANCE ni
            INNER JOIN M_WORKFLOW_NODE_DEFINITION nd
                ON ni.node_definition_id = nd.node_definition_id
            INNER JOIN T_WORKFLOW_INSTANCE wi
                ON ni.workflow_instance_id = wi.workflow_instance_id
            INNER JOIN T_APPLICATION a
                ON wi.application_id = a.application_id
            INNER JOIN M_APPLICATION_TYPE t
                ON a.application_type_id = t.application_type_id
            INNER JOIN T_WORKFLOW_NODE_APPROVER na
                ON ni.node_instance_id = na.node_instance_id
            WHERE ni.node_instance_id = :node_instance_id
              AND na.approver_user_id = :approver_user_id
              AND ni.node_status = 'pending'
        """

        cursor.execute(sql, {
            'node_instance_id': node_instance_id,
            'approver_user_id': approver_user_id
        })
        result = cursor.fetchone()

        if result:
            # 辞書形式に変換（cursor.closeの前に実行）
            columns = [col[0].lower() for col in cursor.description]
            result_dict = dict(zip(columns, result))
            cursor.close()
            return result_dict

        cursor.close()
        return None

    @staticmethod
    def get_approvers_for_node(node_instance_id):
        """
        ノードインスタンスの承認者候補一覧を取得

        Args:
            node_instance_id: ノードインスタンスID

        Returns:
            list: 承認者候補のリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                na.node_approver_id,
                na.node_instance_id,
                na.approver_user_id,
                na.approver_group,
                na.approver_order,
                na.is_notified,
                na.notified_at,
                na.approval_status,
                na.approved_at
            FROM T_WORKFLOW_NODE_APPROVER na
            WHERE na.node_instance_id = :node_instance_id
            ORDER BY na.approver_order
        """

        cursor.execute(sql, {'node_instance_id': node_instance_id})
        results = dict_factory(cursor)

        cursor.close()

        return results

    @staticmethod
    def add_approver(node_instance_id, approver_user_id, approver_order=None, approver_group=None, is_notified='Y'):
        """
        ノードインスタンスに承認者候補を追加

        Args:
            node_instance_id: ノードインスタンスID
            approver_user_id: 承認者のユーザーID
            approver_order: 承認者の優先順位（任意）
            approver_group: 承認者グループ（multiple_deptの場合は所属コード）
            is_notified: メール通知対象フラグ（'Y'/'N'、デフォルト'Y'）

        Returns:
            int: 作成されたノード承認者ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        from datetime import datetime

        # シーケンスからノード承認者IDを取得
        cursor.execute("SELECT SEQ_WORKFLOW_NODE_APPROVER.NEXTVAL FROM DUAL")
        node_approver_id = cursor.fetchone()[0]

        sql = """
            INSERT INTO T_WORKFLOW_NODE_APPROVER (
                node_approver_id,
                node_instance_id,
                approver_user_id,
                approver_group,
                approver_order,
                is_notified,
                approval_status,
                created_at
            ) VALUES (
                :node_approver_id,
                :node_instance_id,
                :approver_user_id,
                :approver_group,
                :approver_order,
                :is_notified,
                :approval_status,
                :created_at
            )
        """

        params = {
            'node_approver_id': node_approver_id,
            'node_instance_id': node_instance_id,
            'approver_user_id': approver_user_id,
            'approver_group': approver_group,
            'approver_order': approver_order,
            'approval_status': 'pending',
            'is_notified': is_notified,
            'created_at': datetime.now()
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return node_approver_id
