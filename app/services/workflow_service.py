"""
ワークフローサービス
ワークフローの開始、進行、完了を管理
"""
from datetime import datetime
from app.models.application import Application
from app.models.application_type import ApplicationType
from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowNodeInstance
from app.models.approval_task import ApprovalTask
from app.models.user import User
from app.utils.db import get_db_connection, dict_fetchone, dict_factory
from app.utils.constants import (
    NODE_TYPE_APPLICANT_DEPT, NODE_TYPE_JURISDICTION_DEPT,
    NODE_TYPE_SPECIFIC_NODE, NODE_TYPE_SPECIFIC_DEPT,
    NODE_TYPE_RESOURCE_DEPT, NODE_TYPE_MULTIPLE_DEPT,
    NODE_STATUS_PENDING, NODE_STATUS_WAITING
)


class WorkflowService:
    """ワークフローサービスクラス"""

    @staticmethod
    def start_workflow(application_id, selected_approvers=None):
        """
        申請に対してワークフローを開始

        Args:
            application_id: 申請ID
            selected_approvers: 選択された承認者情報（辞書）
                {
                    'applicant_dept': ['user1', 'user2'],  # 通知する申請者所属承認者
                    'jurisdiction_dept': ['user3']  # 通知する所管所属承認者
                }

        Returns:
            int: ワークフローインスタンスID

        Raises:
            Exception: ワークフロー開始に失敗した場合
        """
        # 申請情報を取得
        application = Application.get_by_id(application_id)
        if not application:
            raise ValueError(f"申請ID {application_id} が見つかりません")

        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application['application_type_id'])
        if not app_type:
            raise ValueError("申請種類が見つかりません")

        # ワークフロー定義を取得
        workflow_definition_id = app_type['workflow_definition_id']
        workflow_def = WorkflowDefinition.get_by_id(workflow_definition_id)
        if not workflow_def:
            raise ValueError("ワークフロー定義が見つかりません")

        # リソース詳細を取得（skip_condition評価用）
        resource = None
        resource_id = application.get('resource_id')
        if resource_id and app_type.get('resource_detail_query'):
            from app.models.resource import Resource
            try:
                resource = Resource.get_resource_detail(
                    app_type['resource_detail_query'],
                    resource_id
                )
            except Exception as e:
                from flask import current_app
                current_app.logger.warning(f'リソース詳細取得失敗（skip_condition評価用）: {str(e)}')

        # 申請フィールドの値を取得（skip_condition評価用）
        fields = {}
        try:
            from app.models.application_detail import ApplicationDetail
            details = ApplicationDetail.get_by_application(application_id)
            # フィールドコードをキーとした辞書を作成（単一レコードのみ対応）
            for detail in details:
                if detail.get('detail_seq') == 1:  # 単一レコードまたは最初のレコードのみ
                    field_code = detail.get('field_code')
                    if field_code:
                        fields[field_code] = detail.get('field_value')
        except Exception as e:
            from flask import current_app
            current_app.logger.warning(f'申請フィールド取得失敗（skip_condition評価用）: {str(e)}')

        # ワークフローインスタンスを作成
        workflow_instance_id = WorkflowInstance.create(
            application_id,
            workflow_definition_id
        )

        # ノード定義を取得
        node_definitions = WorkflowDefinition.get_nodes(workflow_definition_id)

        # 各ノードインスタンスを作成
        for node_def in node_definitions:
            node_instance_id = WorkflowNodeInstance.create(
                workflow_instance_id,
                node_def['node_definition_id'],
                node_def['node_seq']
            )

            # スキップ条件を評価（リソース詳細とフィールド値も渡す）
            if WorkflowService._should_skip_node(node_def, application, resource, fields):
                WorkflowNodeInstance.update_status(node_instance_id, 'skipped')
                continue

            # 承認者を決定して登録
            approvers = WorkflowService._determine_approvers(node_def, application)
            node_type = node_def['node_type']

            # 所属長承認ノードの場合、is_notifiedを設定
            if selected_approvers:
                if node_type == NODE_TYPE_APPLICANT_DEPT:
                    selected_list = selected_approvers.get('applicant_dept', [])
                elif node_type == NODE_TYPE_JURISDICTION_DEPT:
                    selected_list = selected_approvers.get('jurisdiction_dept', [])
                else:
                    selected_list = None

                # 承認者を登録（is_notifiedフラグ付き）
                # multiple_dept の場合は approvers が辞書のリスト
                if node_type == NODE_TYPE_MULTIPLE_DEPT and isinstance(approvers, list) and len(approvers) > 0 and isinstance(approvers[0], dict):
                    for approver_info in approvers:
                        is_notified = 'Y' if (selected_list is None or approver_info['user_id'] in selected_list) else 'N'
                        ApprovalTask.add_approver(
                            node_instance_id,
                            approver_info['user_id'],
                            approver_group=approver_info.get('approver_group'),
                            is_notified=is_notified
                        )
                else:
                    # 通常のノードタイプ（approversはユーザーIDのリスト）
                    for approver_user_id in approvers:
                        is_notified = 'Y' if (selected_list is None or approver_user_id in selected_list) else 'N'
                        ApprovalTask.add_approver(node_instance_id, approver_user_id, is_notified=is_notified)
            else:
                # 選択情報がない場合は全員に通知
                # multiple_dept の場合は approvers が辞書のリスト
                if node_type == NODE_TYPE_MULTIPLE_DEPT and isinstance(approvers, list) and len(approvers) > 0 and isinstance(approvers[0], dict):
                    for approver_info in approvers:
                        ApprovalTask.add_approver(
                            node_instance_id,
                            approver_info['user_id'],
                            approver_group=approver_info.get('approver_group'),
                            is_notified='Y'
                        )
                else:
                    # 通常のノードタイプ（approversはユーザーIDのリスト）
                    for approver_user_id in approvers:
                        ApprovalTask.add_approver(node_instance_id, approver_user_id, is_notified='Y')

        # 最初の非スキップノードをpendingに更新
        # （注: WorkflowNodeInstance.create()でnode_seq == 1は既にpendingで作成されているが、
        #   最初のノードがskippedの場合は次のノードをpendingにする必要がある）
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT node_instance_id, node_seq
            FROM T_WORKFLOW_NODE_INSTANCE
            WHERE workflow_instance_id = :workflow_instance_id
              AND node_status IN ('waiting', 'pending')
              AND node_status != 'skipped'
            ORDER BY node_seq
            FETCH FIRST 1 ROW ONLY
        """
        cursor.execute(sql, {'workflow_instance_id': workflow_instance_id})
        first_node = dict_fetchone(cursor)
        cursor.close()

        if first_node:
            # 既にpendingの場合はスキップ（node_seq == 1の場合）
            if first_node['node_instance_id']:
                conn2 = get_db_connection()
                cursor2 = conn2.cursor()
                cursor2.execute("""
                    SELECT node_status FROM T_WORKFLOW_NODE_INSTANCE
                    WHERE node_instance_id = :node_instance_id
                """, {'node_instance_id': first_node['node_instance_id']})
                current_status_row = cursor2.fetchone()
                cursor2.close()

                if current_status_row and current_status_row[0] == 'waiting':
                    WorkflowNodeInstance.update_status(first_node['node_instance_id'], 'pending')

            WorkflowInstance.update_current_node(workflow_instance_id, first_node['node_seq'])

        # 申請ステータスを更新
        from flask import current_app
        current_app.logger.info(f'[WorkflowService.start_workflow] 申請ステータスを submitted に更新: application_id={application_id}')
        Application.update_status(application_id, 'submitted')
        current_app.logger.info(f'[WorkflowService.start_workflow] 申請ステータス更新完了: application_id={application_id}')

        return workflow_instance_id

    @staticmethod
    def _should_skip_node(node_def, application, resource=None, fields=None):
        """
        ノードをスキップすべきかを判定

        Args:
            node_def: ノード定義
            application: 申請情報
            resource: リソース詳細情報（任意）
            fields: 申請フィールド値の辞書（field_code: field_value）（任意）

        Returns:
            bool: スキップする場合True
        """
        node_type = node_def['node_type']
        skip_condition = node_def.get('skip_condition')

        # 所管承認のスキップ判定
        if node_type == NODE_TYPE_JURISDICTION_DEPT:
            # 申請者所属 == 所管所属 の場合はスキップ
            applicant_shozoku = application.get('applicant_shozoku')
            jurisdiction_shozoku = application.get('jurisdiction_shozoku')
            if applicant_shozoku == jurisdiction_shozoku:
                return True

        # カスタムスキップ条件の評価
        if skip_condition:
            try:
                # skip_conditionで以下の変数を参照可能にする：
                #   - application.xxx : 申請情報（applicant_shozoku, jurisdiction_shozoku等）
                #   - resource.xxx    : リソース詳細情報（owner_shozoku, top_folder_id等）
                #   - fields.xxx      : 申請フィールド値（フィールドコードでアクセス）
                #
                # 例: "resource.get('top_folder_id') == '12345'"
                #     "fields.get('mailaddress', '').endswith('@nam.co.jp')"
                #     "fields.get('groupname') == 'test-group'"

                # 安全な評価のため、使用可能な変数を明示的に定義
                eval_context = {
                    'application': application,
                    'resource': resource if resource else {},
                    'fields': fields if fields else {}
                }

                # デバッグログ出力
                from flask import current_app
                current_app.logger.debug(f'skip_condition評価: condition={skip_condition}')
                current_app.logger.debug(f'  applicant_shozoku={application.get("applicant_shozoku")} (type={type(application.get("applicant_shozoku"))})')
                current_app.logger.debug(f'  jurisdiction_shozoku={application.get("jurisdiction_shozoku")}')

                # skip_conditionを評価（Pythonの式として）
                result = eval(skip_condition, {"__builtins__": {}}, eval_context)
                current_app.logger.debug(f'  評価結果={result}')
                return bool(result)
            except Exception as e:
                from flask import current_app
                current_app.logger.error(f'スキップ条件の評価エラー: {str(e)}, condition={skip_condition}')
                # エラー時はスキップしない（安全側に倒す）
                return False

        return False

    @staticmethod
    def _determine_approvers(node_def, application):
        """
        ノードの承認者を決定

        Args:
            node_def: ノード定義
            application: 申請情報

        Returns:
            list: 承認者のユーザーIDリスト
        """
        node_type = node_def['node_type']
        approvers = []

        # 申請者所属長承認
        if node_type == NODE_TYPE_APPLICANT_DEPT:
            applicant_shozoku = application.get('applicant_shozoku')
            if applicant_shozoku:
                approver_list = User.get_approvers_by_shozoku(applicant_shozoku)
                approvers = [a['user_id'] for a in approver_list]

        # 所管所属長承認
        elif node_type == NODE_TYPE_JURISDICTION_DEPT:
            jurisdiction_shozoku = application.get('jurisdiction_shozoku')
            if jurisdiction_shozoku:
                approver_list = User.get_approvers_by_shozoku(jurisdiction_shozoku)
                approvers = [a['user_id'] for a in approver_list]

        # 特定ノード承認（M_NODE_APPROVERから取得）
        elif node_type == NODE_TYPE_SPECIFIC_NODE:
            specific_value = node_def.get('specific_value')
            if specific_value:
                # M_NODE_APPROVERから承認者を取得（specific_valueは文字列識別子）
                approver_list = WorkflowService._get_node_approvers(specific_value)
                approvers = [a['approver_user_id'] for a in approver_list]

        # 特定部署承認（e_approverから取得）
        elif node_type == NODE_TYPE_SPECIFIC_DEPT:
            specific_value = node_def.get('specific_value')
            if specific_value:
                # specific_valueに部署コードが格納されている
                # e_approverから該当部署の承認者を取得
                approver_list = User.get_approvers_by_shozoku(specific_value)
                approvers = [a['user_id'] for a in approver_list]

        # リソース所管承認（resource_idとshozokuから承認者を取得）
        elif node_type == NODE_TYPE_RESOURCE_DEPT:
            specific_value = node_def.get('specific_value')
            resource_id = application.get('resource_id')
            applicant_shozoku = application.get('applicant_shozoku')
            if specific_value and resource_id and applicant_shozoku:
                # specific_valueで指定されたテーブル（View）からリソースIDと申請者所属で承認者を取得
                approver_list = User.get_approvers_by_resource_and_shozoku(
                    specific_value, resource_id, applicant_shozoku
                )
                approvers = [a['user_id'] for a in approver_list]

        # 複数所属長承認（複数レコード申請用）
        elif node_type == NODE_TYPE_MULTIPLE_DEPT:
            approvers = WorkflowService._get_multiple_dept_approvers(application)

        return approvers

    @staticmethod
    def _get_node_approvers(specific_value):
        """
        M_NODE_APPROVERから特定ノードの承認者を取得

        Args:
            specific_value: 特定ノード識別子（VARCHAR2文字列）

        Returns:
            list: 承認者のリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                approver_user_id,
                approver_order
            FROM M_NODE_APPROVER
            WHERE specific_node = :specific_value
              AND is_active = 'Y'
            ORDER BY approver_order
        """

        cursor.execute(sql, {'specific_value': specific_value})
        results = dict_factory(cursor)
        cursor.close()

        return results

    @staticmethod
    def _get_multiple_dept_approvers(application):
        """
        複数所属長承認の承認者を取得（複数レコード申請用）

        T_APPLICATION_DETAIL から detail_action が 'modify', 'add', 'delete' で
        field_code='shozoku' のレコードを取得し、その所属の承認者を取得

        Args:
            application: 申請情報

        Returns:
            list: 承認者情報のリスト
                  [
                      {'user_id': 'user1', 'approver_group': '1234567'},
                      {'user_id': 'user2', 'approver_group': '1234567'},
                      {'user_id': 'user3', 'approver_group': '2345678'}
                  ]
                  approver_group は所属コード
        """
        application_id = application.get('application_id')
        application_type_id = application.get('application_type_id')

        if not application_id or not application_type_id:
            return []

        conn = get_db_connection()
        cursor = conn.cursor()

        # field_code='shozoku' のfield_idを取得
        sql_field = """
            SELECT field_id
            FROM M_APPLICATION_FIELD
            WHERE application_type_id = :application_type_id
              AND field_code = 'shozoku'
        """
        cursor.execute(sql_field, {'application_type_id': application_type_id})
        field_result = cursor.fetchone()

        if not field_result:
            cursor.close()
            return []

        field_id = field_result[0]

        # T_APPLICATION_DETAIL から該当するfield_valueを取得
        sql_detail = """
            SELECT DISTINCT field_value
            FROM T_APPLICATION_DETAIL
            WHERE application_id = :application_id
              AND field_id = :field_id
              AND detail_action IN ('modify', 'add', 'delete')
              AND field_value IS NOT NULL
        """
        cursor.execute(sql_detail, {
            'application_id': application_id,
            'field_id': field_id
        })
        shozoku_results = cursor.fetchall()
        cursor.close()

        if not shozoku_results:
            return []

        # 各所属の承認者を取得（所属グループ付き）
        approvers_list = []
        seen = set()  # 重複排除用（user_idのみで判定）

        for row in shozoku_results:
            shozoku = row[0]
            if shozoku:
                approver_list = User.get_approvers_by_shozoku(shozoku)
                for approver in approver_list:
                    user_id = approver['user_id']
                    # 同一ユーザーが複数所属の承認者になる場合は最初の所属のみ
                    if user_id not in seen:
                        approvers_list.append({
                            'user_id': user_id,
                            'approver_group': shozoku
                        })
                        seen.add(user_id)

        return approvers_list

    @staticmethod
    def _is_node_fully_approved(node_instance_id):
        """
        ノードが完全に承認されたかチェック（グループ別承認対応）

        Args:
            node_instance_id: ノードインスタンスID

        Returns:
            bool: 全承認者が approved または completed_by_peer であればTrue
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # 承認者情報を取得（is_notified条件は不要 - メール通知とは無関係）
        sql = """
            SELECT
                approver_user_id,
                approver_group,
                approval_status
            FROM T_WORKFLOW_NODE_APPROVER
            WHERE node_instance_id = :node_instance_id
        """
        cursor.execute(sql, {'node_instance_id': node_instance_id})
        approvers = dict_factory(cursor)
        cursor.close()

        if not approvers:
            return False

        # approver_group がすべて NULL の場合は通常の承認判定
        has_groups = any(a['approver_group'] for a in approvers)

        if not has_groups:
            # 通常ノード：全承認者が approved または completed_by_peer であればOK
            return all(a['approval_status'] in ('approved', 'completed_by_peer') for a in approvers)
        else:
            # グループ別承認ノード（multiple_dept）：全グループから最低1人承認が必要
            # 必要なグループを取得
            required_groups = set([a['approver_group'] for a in approvers if a['approver_group']])

            # 承認済みのグループを取得（approval_status='approved'のグループ）
            approved_groups = set([a['approver_group'] for a in approvers if a['approval_status'] == 'approved' and a['approver_group']])

            # 全てのグループから承認されているか
            return approved_groups >= required_groups

    @staticmethod
    def approve_node(node_instance_id, approver_user_id, comment=None):
        """
        ノードを承認

        Args:
            node_instance_id: ノードインスタンスID
            approver_user_id: 承認者のユーザーID
            comment: 承認コメント

        Returns:
            bool: 成功時True
        """
        # 承認者の承認日時を記録
        conn = get_db_connection()
        cursor = conn.cursor()

        # まず承認者のapprover_groupを取得
        sql_get_group = """
            SELECT approver_group
            FROM T_WORKFLOW_NODE_APPROVER
            WHERE node_instance_id = :node_instance_id
              AND approver_user_id = :approver_user_id
        """
        cursor.execute(sql_get_group, {
            'node_instance_id': node_instance_id,
            'approver_user_id': approver_user_id
        })
        result = dict_fetchone(cursor)
        approver_group = result['approver_group'] if result else None

        # 承認者本人のステータスを更新
        sql = """
            UPDATE T_WORKFLOW_NODE_APPROVER
            SET approval_status = :approval_status,
                approved_at = :approved_at,
                action_comment = :action_comment
            WHERE node_instance_id = :node_instance_id
              AND approver_user_id = :approver_user_id
        """
        cursor.execute(sql, {
            'approval_status': 'approved',
            'approved_at': datetime.now(),
            'action_comment': comment,
            'node_instance_id': node_instance_id,
            'approver_user_id': approver_user_id
        })

        # 同じグループまたは同じノードの他の承認者を completed_by_peer に更新
        if approver_group:
            # グループ承認の場合：同じグループの他の承認者のみ completed_by_peer に
            sql_update_peers = """
                UPDATE T_WORKFLOW_NODE_APPROVER
                SET approval_status = 'completed_by_peer'
                WHERE node_instance_id = :node_instance_id
                  AND approver_group = :approver_group
                  AND approver_user_id != :approver_user_id
                  AND approval_status = 'pending'
            """
            cursor.execute(sql_update_peers, {
                'node_instance_id': node_instance_id,
                'approver_group': approver_group,
                'approver_user_id': approver_user_id
            })
        else:
            # 通常承認の場合：同じノードの全ての他の承認者を completed_by_peer に
            sql_update_peers = """
                UPDATE T_WORKFLOW_NODE_APPROVER
                SET approval_status = 'completed_by_peer'
                WHERE node_instance_id = :node_instance_id
                  AND approver_user_id != :approver_user_id
                  AND approval_status = 'pending'
                  AND (approver_group IS NULL OR approver_group = '')
            """
            cursor.execute(sql_update_peers, {
                'node_instance_id': node_instance_id,
                'approver_user_id': approver_user_id
            })

        conn.commit()

        # 全グループから承認されたかチェック
        if WorkflowService._is_node_fully_approved(node_instance_id):
            # ノードを承認済みに更新
            WorkflowNodeInstance.update_status(
                node_instance_id,
                'approved',
                approver_user_id,
                comment
            )

            # 次のノードに進める
            return WorkflowService._advance_to_next_node(node_instance_id)

        cursor.close()
        return True

    @staticmethod
    def reject_node(node_instance_id, approver_user_id, comment=None):
        """
        ノードを却下

        Args:
            node_instance_id: ノードインスタンスID
            approver_user_id: 承認者のユーザーID
            comment: 却下理由

        Returns:
            bool: 成功時True
        """
        # 承認者の却下日時を記録
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE T_WORKFLOW_NODE_APPROVER
            SET approval_status = :approval_status,
                approved_at = :approved_at,
                action_comment = :action_comment
            WHERE node_instance_id = :node_instance_id
              AND approver_user_id = :approver_user_id
        """
        cursor.execute(sql, {
            'approval_status': 'rejected',
            'approved_at': datetime.now(),
            'action_comment': comment,
            'node_instance_id': node_instance_id,
            'approver_user_id': approver_user_id
        })
        conn.commit()
        cursor.close()

        # ノードを却下に更新
        WorkflowNodeInstance.update_status(
            node_instance_id,
            'rejected',
            approver_user_id,
            comment
        )

        # ワークフローインスタンスIDを取得
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT workflow_instance_id
            FROM T_WORKFLOW_NODE_INSTANCE
            WHERE node_instance_id = :node_instance_id
        """
        cursor.execute(sql, {'node_instance_id': node_instance_id})
        result = dict_fetchone(cursor)
        cursor.close()

        if not result:
            return False

        workflow_instance_id = result['workflow_instance_id']

        # ワークフローインスタンスを却下ステータスに更新
        WorkflowInstance.complete(workflow_instance_id, 'rejected')

        # 申請のステータスをdraftに戻す（申請者が削除または修正できるように）
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT application_id
            FROM T_WORKFLOW_INSTANCE
            WHERE workflow_instance_id = :workflow_instance_id
        """
        cursor.execute(sql, {'workflow_instance_id': workflow_instance_id})
        result = dict_fetchone(cursor)
        cursor.close()

        if result:
            application_id = result['application_id']
            Application.update_status(application_id, 'draft')

        return True

    @staticmethod
    def _advance_to_next_node(current_node_instance_id):
        """
        次のノードに進める

        Args:
            current_node_instance_id: 現在のノードインスタンスID

        Returns:
            bool: 成功時True
        """
        from app.models.workflow import WorkflowInstance
        from app.models.application import Application
        from flask import current_app

        # 現在のノードインスタンスの情報を取得
        all_nodes = []
        current_node = None
        workflow_instance_id = None

        # ノード一覧から現在のノードを探す
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                node_instance_id,
                workflow_instance_id,
                node_seq,
                node_status
            FROM T_WORKFLOW_NODE_INSTANCE
            WHERE node_instance_id = :node_instance_id
        """
        cursor.execute(sql, {'node_instance_id': current_node_instance_id})
        result = dict_fetchone(cursor)

        if not result:
            cursor.close()
            return False

        workflow_instance_id = result['workflow_instance_id']
        current_seq = result['node_seq']

        # 同じワークフローの全ノードを取得（node_typeも取得）
        sql = """
            SELECT
                ni.node_instance_id,
                ni.node_seq,
                ni.node_status,
                ni.node_definition_id,
                nd.node_type,
                nd.specific_value
            FROM T_WORKFLOW_NODE_INSTANCE ni
            INNER JOIN M_WORKFLOW_NODE_DEFINITION nd
                ON ni.node_definition_id = nd.node_definition_id
            WHERE ni.workflow_instance_id = :workflow_instance_id
            ORDER BY ni.node_seq
        """
        cursor.execute(sql, {'workflow_instance_id': workflow_instance_id})
        all_nodes = dict_factory(cursor)
        cursor.close()

        # 次のノードを探す
        next_node = None
        for node in all_nodes:
            if node['node_seq'] > current_seq:
                # スキップされていないノードを探す
                if node['node_status'] != 'skipped':
                    next_node = node
                    break

        if next_node:
            # 次のノードをpendingに更新
            WorkflowNodeInstance.update_status(next_node['node_instance_id'], 'pending')

            # ワークフローインスタンスの現在ノードを更新
            WorkflowInstance.update_current_node(workflow_instance_id, next_node['node_seq'])

            # node_type='auto' の場合は外部の自動処理システムが処理を実行
            # ワークフローシステムは pending にするだけ
            if next_node.get('node_type') == 'auto':
                current_app.logger.info(
                    f"[WorkflowService] 自動処理ノード到達: node_instance_id={next_node['node_instance_id']}, "
                    f"process_code={next_node.get('specific_value')}"
                )
                # 外部の自動処理システムが pending ノードを検出して処理を実行
                # 処理完了後、自動処理システムが approved または failed に更新

            return True
        else:
            # 次のノードがない = ワークフロー完了
            WorkflowInstance.complete(workflow_instance_id, 'completed')

            # 申請ステータスを承認済みに更新
            # application_idを取得
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = "SELECT application_id FROM T_WORKFLOW_INSTANCE WHERE workflow_instance_id = :workflow_instance_id"
            cursor.execute(sql, {'workflow_instance_id': workflow_instance_id})
            result = dict_fetchone(cursor)
            cursor.close()

            if result:
                Application.update_status(result['application_id'], 'approved')

            return True

    @staticmethod
    def return_node(node_instance_id, approver_user_id, comment=None):
        """
        ノードを差し戻し（申請をdraftに戻す）

        Args:
            node_instance_id: ノードインスタンスID
            approver_user_id: 承認者のユーザーID
            comment: 差し戻し理由

        Returns:
            bool: 成功時True
        """
        # 承認者の差し戻し日時を記録
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE T_WORKFLOW_NODE_APPROVER
            SET approval_status = :approval_status,
                approved_at = :approved_at,
                action_comment = :action_comment
            WHERE node_instance_id = :node_instance_id
              AND approver_user_id = :approver_user_id
        """
        cursor.execute(sql, {
            'approval_status': 'returned',
            'approved_at': datetime.now(),
            'action_comment': comment,
            'node_instance_id': node_instance_id,
            'approver_user_id': approver_user_id
        })
        conn.commit()
        cursor.close()

        # ノードを差し戻しに更新
        WorkflowNodeInstance.update_status(
            node_instance_id,
            'returned',
            approver_user_id,
            comment
        )

        # ワークフローインスタンスIDを取得
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT workflow_instance_id
            FROM T_WORKFLOW_NODE_INSTANCE
            WHERE node_instance_id = :node_instance_id
        """
        cursor.execute(sql, {'node_instance_id': node_instance_id})
        result = dict_fetchone(cursor)
        cursor.close()

        if not result:
            return False

        workflow_instance_id = result['workflow_instance_id']

        # ワークフローインスタンスを停止（returned ステータス）
        WorkflowInstance.complete(workflow_instance_id, 'returned')

        # 申請のステータスをdraftに戻す
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT application_id
            FROM T_WORKFLOW_INSTANCE
            WHERE workflow_instance_id = :workflow_instance_id
        """
        cursor.execute(sql, {'workflow_instance_id': workflow_instance_id})
        result = dict_fetchone(cursor)
        cursor.close()

        if result:
            application_id = result['application_id']
            Application.update_status(application_id, 'draft')

        return True

    @staticmethod
    def recall_node(node_instance_id, user_id):
        """
        承認済みノードを引き戻し（承認を取り消して再処理可能にする）

        Args:
            node_instance_id: ノードインスタンスID
            user_id: 引き戻しを実行するユーザーID

        Returns:
            bool: 成功時True
        """
        # ノード情報を取得
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                ni.node_instance_id,
                ni.workflow_instance_id,
                ni.node_seq,
                ni.node_status,
                ni.assigned_user_id
            FROM T_WORKFLOW_NODE_INSTANCE ni
            WHERE ni.node_instance_id = :node_instance_id
        """
        cursor.execute(sql, {'node_instance_id': node_instance_id})
        current_node = dict_fetchone(cursor)
        cursor.close()

        if not current_node:
            return False

        # ステータスチェック：承認待ち中または承認済みのみ引き戻し可能
        if current_node['node_status'] not in ('pending', 'approved'):
            raise ValueError('承認待ち中または承認済みのノードのみ引き戻し可能です')

        # 権限チェック：そのノードの承認者で、かつ自分が承認済みであること
        from app.models.approval_task import ApprovalTask
        approvers = ApprovalTask.get_approvers_for_node(node_instance_id)

        my_approval = next((a for a in approvers if a['approver_user_id'] == user_id and a.get('approval_status') == 'approved'), None)

        if not my_approval:
            raise ValueError('このノードで承認した人のみ引き戻し可能です')

        workflow_instance_id = current_node['workflow_instance_id']
        current_seq = current_node['node_seq']

        # 同じワークフローの全ノードを取得
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT
                node_instance_id,
                node_seq,
                node_status
            FROM T_WORKFLOW_NODE_INSTANCE
            WHERE workflow_instance_id = :workflow_instance_id
            ORDER BY node_seq
        """
        cursor.execute(sql, {'workflow_instance_id': workflow_instance_id})
        all_nodes = dict_factory(cursor)
        cursor.close()

        # 次のノードを確認
        next_node = None
        for node in all_nodes:
            if node['node_seq'] > current_seq and node['node_status'] != 'skipped':
                next_node = node
                break

        # 次のノードがない、または既に承認済みの場合は引き戻し不可
        if not next_node:
            raise ValueError('最終ノードは引き戻しできません')

        if next_node['node_status'] not in ('pending', 'waiting'):
            raise ValueError('次のノードが既に処理されているため引き戻しできません')

        # 自分のノードを pending に戻す
        WorkflowNodeInstance.update_status(node_instance_id, 'pending')

        # 自分の承認をpendingに戻す
        conn = get_db_connection()
        cursor = conn.cursor()

        # まず自分のapprover_groupを取得
        sql_get_group = """
            SELECT approver_group
            FROM T_WORKFLOW_NODE_APPROVER
            WHERE node_instance_id = :node_instance_id
              AND approver_user_id = :user_id
        """
        cursor.execute(sql_get_group, {
            'node_instance_id': node_instance_id,
            'user_id': user_id
        })
        result = dict_fetchone(cursor)
        approver_group = result['approver_group'] if result else None

        # 自分の承認ステータスをpendingに戻す
        sql_reset_self = """
            UPDATE T_WORKFLOW_NODE_APPROVER
            SET approval_status = 'pending',
                approved_at = NULL,
                action_comment = NULL
            WHERE node_instance_id = :node_instance_id
              AND approver_user_id = :user_id
        """
        cursor.execute(sql_reset_self, {
            'node_instance_id': node_instance_id,
            'user_id': user_id
        })

        # 同じグループまたは同じノードのcompleted_by_peerもpendingに戻す
        if approver_group:
            # グループ承認の場合：同じグループのcompleted_by_peerのみpendingに戻す
            sql_reset_peers = """
                UPDATE T_WORKFLOW_NODE_APPROVER
                SET approval_status = 'pending'
                WHERE node_instance_id = :node_instance_id
                  AND approver_group = :approver_group
                  AND approver_user_id != :user_id
                  AND approval_status = 'completed_by_peer'
            """
            cursor.execute(sql_reset_peers, {
                'node_instance_id': node_instance_id,
                'approver_group': approver_group,
                'user_id': user_id
            })
        else:
            # 通常承認の場合：同じノードの全てのcompleted_by_peerをpendingに戻す
            sql_reset_peers = """
                UPDATE T_WORKFLOW_NODE_APPROVER
                SET approval_status = 'pending'
                WHERE node_instance_id = :node_instance_id
                  AND approver_user_id != :user_id
                  AND approval_status = 'completed_by_peer'
                  AND (approver_group IS NULL OR approver_group = '')
            """
            cursor.execute(sql_reset_peers, {
                'node_instance_id': node_instance_id,
                'user_id': user_id
            })

        conn.commit()
        cursor.close()

        # 次のノード以降を waiting に戻す
        for node in all_nodes:
            if node['node_seq'] > current_seq and node['node_status'] != 'skipped':
                WorkflowNodeInstance.update_status(node['node_instance_id'], 'waiting')

        # ワークフローインスタンスの current_node_seq を引き戻したノードに戻す
        WorkflowInstance.update_current_node(workflow_instance_id, current_seq)

        # ワークフローは in_progress のまま（終了しない）
        # 申請ステータスも submitted のまま（変更しない）

        return True

