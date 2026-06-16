"""
申請データモデル
"""
from datetime import datetime
from app.utils.db import get_db_connection, dict_fetchone, dict_factory


class Application:
    """申請モデル"""

    @staticmethod
    def create(application_data):
        """
        申請を新規作成（ドラフト状態）

        Args:
            application_data: 申請データ（dict）
                - application_type_id
                - action_type
                - applicant_user_id
                - applicant_shozoku
                - jurisdiction_shozoku (optional)
                - application_title
                - reference_resource_id (optional)
                - remarks (optional)

        Returns:
            int: 作成された申請ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # シーケンスから申請IDを取得
        cursor.execute("SELECT SEQ_APPLICATION.NEXTVAL FROM DUAL")
        application_id = cursor.fetchone()[0]

        now = datetime.now()

        sql = """
            INSERT INTO T_APPLICATION (
                application_id,
                application_type_id,
                action_type,
                applicant_user_id,
                applicant_shozoku,
                jurisdiction_shozoku,
                application_title,
                application_status,
                reference_resource_id,
                scheduled_date,
                remarks,
                created_at,
                updated_at
            ) VALUES (
                :application_id,
                :application_type_id,
                :action_type,
                :applicant_user_id,
                :applicant_shozoku,
                :jurisdiction_shozoku,
                :application_title,
                'draft',
                :reference_resource_id,
                :scheduled_date,
                :remarks,
                :created_at,
                :updated_at
            )
        """

        params = {
            'application_id': application_id,
            'application_type_id': application_data['application_type_id'],
            'action_type': application_data['action_type'],
            'applicant_user_id': application_data['applicant_user_id'],
            'applicant_shozoku': application_data['applicant_shozoku'],
            'jurisdiction_shozoku': application_data.get('jurisdiction_shozoku'),
            'application_title': application_data['application_title'],
            'reference_resource_id': application_data.get('reference_resource_id') or application_data.get('resource_id'),
            'scheduled_date': application_data.get('scheduled_date'),
            'remarks': application_data.get('remarks'),
            'created_at': now,
            'updated_at': now
        }

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()

        return application_id

    @staticmethod
    def get_by_id(application_id):
        """
        申請IDから申請情報を取得

        Args:
            application_id: 申請ID

        Returns:
            dict: 申請情報
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
                a.current_workflow_node_id,
                a.reference_resource_id AS resource_id,
                a.created_at,
                a.updated_at,
                a.submitted_at,
                a.completed_at,
                a.remarks,
                t.application_type_name,
                t.application_type_code
            FROM T_APPLICATION a
            INNER JOIN M_APPLICATION_TYPE t
                ON a.application_type_id = t.application_type_id
            WHERE a.application_id = :application_id
        """

        cursor.execute(sql, {'application_id': application_id})
        result = dict_fetchone(cursor)

        cursor.close()

        return result

    @staticmethod
    def get_by_applicant(applicant_user_id, status=None):
        """
        申請者のユーザーIDから申請一覧を取得

        Args:
            applicant_user_id: 申請者のユーザーID
            status: 申請ステータス（任意）

        Returns:
            list: 申請のリスト
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
                a.application_title,
                a.application_status,
                a.created_at,
                a.submitted_at,
                a.completed_at,
                t.application_type_name
            FROM T_APPLICATION a
            INNER JOIN M_APPLICATION_TYPE t
                ON a.application_type_id = t.application_type_id
            WHERE a.applicant_user_id = :applicant_user_id
              AND a.application_status != 'deleted'
        """

        params = {'applicant_user_id': applicant_user_id}

        if status:
            sql += " AND a.application_status = :status"
            params['status'] = status

        sql += " ORDER BY a.created_at DESC"

        cursor.execute(sql, params)
        results = dict_factory(cursor)

        cursor.close()

        return results

    @staticmethod
    def get_integrated_task_list(user_id):
        """
        統合タスク一覧を取得
        - 自分が申請したもの
        - 自分が承認者となっているもの
        - 完了済み（approved/rejected）は1週間以内のみ

        Args:
            user_id: ユーザーID

        Returns:
            list: 統合タスクのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT DISTINCT
                a.application_id,
                a.application_type_id,
                a.action_type,
                a.applicant_user_id,
                a.applicant_shozoku,
                a.application_title,
                a.application_status,
                a.created_at,
                a.submitted_at,
                a.completed_at,
                t.application_type_name,
                CASE
                    WHEN a.applicant_user_id = :user_id THEN 'applicant'
                    ELSE 'approver'
                END AS user_role,
                (
                    SELECT COUNT(*)
                    FROM T_WORKFLOW_INSTANCE wi
                    INNER JOIN T_WORKFLOW_NODE_INSTANCE ni ON wi.workflow_instance_id = ni.workflow_instance_id
                    INNER JOIN T_WORKFLOW_NODE_APPROVER na ON ni.node_instance_id = na.node_instance_id
                    WHERE wi.application_id = a.application_id
                      AND na.approver_user_id = :user_id
                      AND ni.node_status = 'pending'
                      AND na.approval_status = 'pending'
                      AND wi.workflow_status = 'in_progress'
                ) AS pending_task_count
            FROM T_APPLICATION a
            INNER JOIN M_APPLICATION_TYPE t ON a.application_type_id = t.application_type_id
            WHERE a.application_status != 'deleted'
              AND (
                  -- 自分が申請者
                  a.applicant_user_id = :user_id
                  OR
                  -- 自分が承認者（承認タスクがある）
                  EXISTS (
                      SELECT 1
                      FROM T_WORKFLOW_INSTANCE wi
                      INNER JOIN T_WORKFLOW_NODE_INSTANCE ni ON wi.workflow_instance_id = ni.workflow_instance_id
                      INNER JOIN T_WORKFLOW_NODE_APPROVER na ON ni.node_instance_id = na.node_instance_id
                      WHERE wi.application_id = a.application_id
                        AND na.approver_user_id = :user_id
                        AND ni.node_status != 'skipped'
                        AND wi.workflow_status = 'in_progress'
                  )
              )
              AND (
                  -- 進行中・下書きは全て表示
                  a.application_status IN ('draft', 'submitted')
                  OR
                  -- 完了済み（approved）は1週間以内のみ
                  (a.application_status = 'approved'
                   AND a.completed_at >= SYSTIMESTAMP - INTERVAL '7' DAY)
              )
            ORDER BY
                CASE
                    WHEN a.application_status = 'draft' THEN 1
                    WHEN a.application_status = 'submitted' THEN 2
                    ELSE 3
                END,
                a.created_at DESC
        """

        cursor.execute(sql, {'user_id': user_id})
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def update_status(application_id, status, workflow_node_id=None):
        """
        申請のステータスを更新

        Args:
            application_id: 申請ID
            status: 新しいステータス
            workflow_node_id: 現在のワークフローノードID（任意）

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        now = datetime.now()

        sql = """
            UPDATE T_APPLICATION
            SET application_status = :status,
                current_workflow_node_id = :workflow_node_id,
                updated_at = :updated_at
        """

        params = {
            'status': status,
            'workflow_node_id': workflow_node_id,
            'updated_at': now,
            'application_id': application_id
        }

        # ステータスに応じて追加の日時を更新
        if status == 'submitted':
            sql += ", submitted_at = :submitted_at"
            params['submitted_at'] = now
        elif status in ['approved', 'rejected', 'withdrawn']:
            sql += ", completed_at = :completed_at"
            params['completed_at'] = now

        sql += " WHERE application_id = :application_id"

        cursor.execute(sql, params)
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0

    @staticmethod
    def update(application_id, application_data):
        """
        申請の基本情報を更新

        Args:
            application_id: 申請ID
            application_data: 更新する申請データ（辞書）

        Returns:
            bool: 更新成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        now = datetime.now()

        sql = """
            UPDATE T_APPLICATION
            SET application_title = :application_title,
                remarks = :remarks,
                updated_at = :updated_at
            WHERE application_id = :application_id
        """

        params = {
            'application_title': application_data.get('application_title'),
            'remarks': application_data.get('remarks'),
            'updated_at': now,
            'application_id': application_id
        }

        cursor.execute(sql, params)
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0

    @staticmethod
    def delete(application_id):
        """
        申請を論理削除（ステータスを 'deleted' に更新）

        Args:
            application_id: 申請ID

        Returns:
            bool: 削除成功時True
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        now = datetime.now()

        sql = """
            UPDATE T_APPLICATION
            SET application_status = 'deleted',
                completed_at = :completed_at,
                updated_at = :updated_at
            WHERE application_id = :application_id
        """

        params = {
            'completed_at': now,
            'updated_at': now,
            'application_id': application_id
        }

        cursor.execute(sql, params)
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()

        return rows_updated > 0
