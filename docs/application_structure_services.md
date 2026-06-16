# Flaskアプリケーション構成案 - Services & Routes

## 3. Services（ビジネスロジック層）

### 3.1 app/services/application_service.py

```python
"""
申請処理サービス
"""
from app.models.application import Application, ApplicationDetail
from app.models.master import ApplicationType, ApplicationField
from app.services.validation_service import ValidationService
from app.services.workflow_service import WorkflowService


class ApplicationService:
    """申請処理サービス"""
    
    @staticmethod
    def create_draft(user_id, application_type_id, action_type, data):
        """
        下書きを作成
        
        Args:
            user_id: ユーザーID
            application_type_id: 申請種類ID
            action_type: 申請区分
            data: 申請データ
        
        Returns:
            int: 作成された申請ID
        """
        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type:
            raise ValueError("申請種類が見つかりません")
        
        # 申請区分のサポート確認
        if action_type == 'create' and app_type['support_create'] != 'Y':
            raise ValueError("この申請種類は新規作成をサポートしていません")
        
        # 申請者の所属を取得
        from app.models.user import User
        user = User.get_by_id(user_id)
        applicant_shozoku = data.get('applicant_shozoku') or user['shozoku']
        
        # 申請基本情報を作成
        application_data = {
            'application_type_id': application_type_id,
            'action_type': action_type,
            'applicant_user_id': user_id,
            'applicant_shozoku': applicant_shozoku,
            'target_user_id': data.get('target_user_id'),
            'target_shozoku': data.get('target_shozoku'),
            'jurisdiction_shozoku': data.get('jurisdiction_shozoku'),
            'application_title': data.get('application_title', ''),
            'remarks': data.get('remarks')
        }
        
        application_id = Application.create(application_data)
        
        # 申請詳細を作成
        if data.get('details'):
            ApplicationDetail.create_batch(application_id, data['details'])
        
        return application_id
    
    
    @staticmethod
    def update_draft(application_id, user_id, data):
        """
        下書きを更新
        
        Args:
            application_id: 申請ID
            user_id: ユーザーID
            data: 更新データ
        
        Returns:
            bool: 成功したかどうか
        """
        # 申請を取得
        application = Application.get_by_id(application_id)
        if not application:
            raise ValueError("申請が見つかりません")
        
        # 申請者チェック
        if application['applicant_user_id'] != user_id:
            raise PermissionError("この申請を更新する権限がありません")
        
        # 下書きチェック
        if application['application_status'] != 'draft':
            raise ValueError("下書き状態の申請のみ更新できます")
        
        # 更新
        Application.update(application_id, data)
        
        # 詳細データの更新
        if data.get('details'):
            # 既存の詳細データを削除
            ApplicationDetail.delete_by_application_id(application_id)
            # 新しい詳細データを登録
            ApplicationDetail.create_batch(application_id, data['details'])
        
        return True
    
    
    @staticmethod
    def submit_application(application_id, user_id):
        """
        申請を提出
        
        Args:
            application_id: 申請ID
            user_id: ユーザーID
        
        Returns:
            bool: 成功したかどうか
        """
        # 申請を取得
        application = Application.get_by_id(application_id)
        if not application:
            raise ValueError("申請が見つかりません")
        
        # 申請者チェック
        if application['applicant_user_id'] != user_id:
            raise PermissionError("この申請を提出する権限がありません")
        
        # 下書きチェック
        if application['application_status'] != 'draft':
            raise ValueError("下書き状態の申請のみ提出できます")
        
        # バリデーション
        ValidationService.validate_application(application_id)
        
        # 申請を提出状態に変更
        Application.submit(application_id)
        
        # ワークフローを開始
        WorkflowService.start_workflow(application_id)
        
        return True
    
    
    @staticmethod
    def get_application_form_fields(application_type_id, action_type):
        """
        申請フォームのフィールド定義を取得
        
        Args:
            application_type_id: 申請種類ID
            action_type: 申請区分
        
        Returns:
            list: フィールド定義のリスト
        """
        fields = ApplicationField.get_by_application_type(application_type_id)
        
        # 申請区分に応じてフィールドをフィルタ・調整
        form_fields = []
        for field in fields:
            # 必須フラグの判定
            is_required = False
            if action_type == 'create':
                is_required = field['is_required_create'] == 'Y'
            elif action_type == 'modify':
                is_required = field['is_required_modify'] == 'Y'
            elif action_type == 'delete':
                is_required = field['is_required_delete'] == 'Y'
            
            # 編集可能フラグの判定
            is_editable = True
            if action_type == 'modify':
                is_editable = field['is_editable_modify'] == 'Y'
            elif action_type == 'delete':
                is_editable = False  # 削除時はすべて読み取り専用
            
            form_fields.append({
                'field_id': field['field_id'],
                'field_code': field['field_code'],
                'field_name': field['field_name'],
                'field_type': field['field_type'],
                'is_required': is_required,
                'is_editable': is_editable,
                'is_multi_row': field['is_multi_row'] == 'Y',
                'validation_rule_id': field['validation_rule_id'],
                'pulldown_group_id': field['pulldown_group_id'],
                'default_value': field['default_value'],
                'placeholder': field['placeholder'],
                'help_text': field['help_text']
            })
        
        return form_fields
```

---

### 3.2 app/services/workflow_service.py

```python
"""
ワークフロー処理サービス
"""
from app.models.workflow import WorkflowInstance, WorkflowNodeInstance, WorkflowNodeApprover
from app.models.application import Application
from app.models.master import WorkflowDefinition, WorkflowNodeDefinition
from app.models.user import User
from app.services.notification_service import NotificationService


class WorkflowService:
    """ワークフロー処理サービス"""
    
    @staticmethod
    def start_workflow(application_id):
        """
        ワークフローを開始
        
        Args:
            application_id: 申請ID
        
        Returns:
            int: ワークフローインスタンスID
        """
        # 申請を取得
        application = Application.get_by_id(application_id)
        if not application:
            raise ValueError("申請が見つかりません")
        
        # ワークフロー定義を取得
        from app.models.master import ApplicationType
        app_type = ApplicationType.get_by_id(application['application_type_id'])
        workflow_definition_id = app_type['workflow_definition_id']
        
        # ワークフローインスタンスを作成
        workflow_instance_id = WorkflowInstance.create(application_id, workflow_definition_id)
        
        # ノード定義を取得
        node_definitions = WorkflowNodeDefinition.get_by_workflow(workflow_definition_id)
        
        # 全ノードインスタンスを作成
        for node_def in node_definitions:
            node_status = 'pending' if node_def['node_seq'] == 1 else 'waiting'
            node_instance_id = WorkflowNodeInstance.create(
                workflow_instance_id,
                node_def['node_definition_id'],
                node_def['node_seq'],
                node_status
            )
            
            # 最初のノードの場合、承認者候補を登録
            if node_def['node_seq'] == 1:
                WorkflowService._register_approvers(node_instance_id, node_def, application)
        
        return workflow_instance_id
    
    
    @staticmethod
    def _register_approvers(node_instance_id, node_def, application):
        """
        ノードの承認者候補を登録
        
        Args:
            node_instance_id: ノードインスタンスID
            node_def: ノード定義
            application: 申請情報
        """
        # スキップ条件をチェック
        if WorkflowService._should_skip_node(node_def, application):
            WorkflowNodeInstance.update_status(node_instance_id, 'skipped')
            return
        
        # 承認者候補を取得
        approvers = WorkflowService._get_approvers_for_node(node_def, application)
        
        if not approvers:
            raise Exception(f"承認者が見つかりません: node_seq={node_def['node_seq']}")
        
        # ノードを承認待ち状態に設定
        from datetime import datetime
        WorkflowNodeInstance.set_arrived(node_instance_id, datetime.now())
        
        # 承認者候補を登録
        WorkflowNodeApprover.create_batch(node_instance_id, approvers)
        
        # 承認者に通知
        NotificationService.notify_approvers(node_instance_id, approvers, application)
    
    
    @staticmethod
    def _should_skip_node(node_def, application):
        """
        ノードをスキップすべきか判定
        
        Args:
            node_def: ノード定義
            application: 申請情報
        
        Returns:
            bool: スキップする場合True
        """
        if not node_def.get('skip_condition'):
            return False
        
        # スキップ条件を評価（簡易実装）
        condition = node_def['skip_condition']
        
        # 例: "applicant_shozoku = jurisdiction_shozoku"
        if condition == 'applicant_shozoku = jurisdiction_shozoku':
            return application['applicant_shozoku'] == application['jurisdiction_shozoku']
        
        # 例: "target_user_id IS NULL"
        if condition == 'target_user_id IS NULL':
            return application['target_user_id'] is None
        
        return False
    
    
    @staticmethod
    def _get_approvers_for_node(node_def, application):
        """
        ノードの承認者候補を取得
        
        Args:
            node_def: ノード定義
            application: 申請情報
        
        Returns:
            list: 承認者リスト
        """
        node_type = node_def['node_type']
        
        if node_type == 'applicant_dept':
            # 申請者の所属長
            return User.get_approvers_by_shozoku(application['applicant_shozoku'])
        
        elif node_type == 'target_dept':
            # 申請対象ユーザーの所属長
            if application['target_shozoku']:
                return User.get_approvers_by_shozoku(application['target_shozoku'])
            return []
        
        elif node_type == 'jurisdiction_dept':
            # 所管所属長
            if application['jurisdiction_shozoku']:
                return User.get_approvers_by_shozoku(application['jurisdiction_shozoku'])
            return []
        
        elif node_type == 'specific_dept':
            # 特定所属
            return User.get_approvers_by_shozoku(node_def['specific_shozoku'])
        
        elif node_type == 'final':
            # 最終承認者（ノード承認者マスタから取得）
            from app.models.master import NodeApprover
            return NodeApprover.get_by_node_definition(node_def['node_definition_id'])
        
        return []
    
    
    @staticmethod
    def advance_to_next_node(workflow_instance_id):
        """
        次のノードへ進む
        
        Args:
            workflow_instance_id: ワークフローインスタンスID
        
        Returns:
            bool: 成功したかどうか
        """
        workflow = WorkflowInstance.get_by_id(workflow_instance_id)
        application = Application.get_by_id(workflow['application_id'])
        current_node_seq = workflow['current_node_seq']
        
        # 次のノードを取得
        next_node = WorkflowNodeInstance.get_by_seq(workflow_instance_id, current_node_seq + 1)
        
        if not next_node:
            # 最終ノードまで完了
            WorkflowInstance.complete(workflow_instance_id)
            Application.set_status(application['application_id'], 'approved')
            
            # 自動設定処理を実行
            # TODO: 自動設定処理の実装
            
            return True
        
        # 次のノード定義を取得
        from app.models.master import WorkflowNodeDefinition
        next_node_def = WorkflowNodeDefinition.get_by_id(next_node['node_definition_id'])
        
        # 次のノードの承認者候補を登録
        WorkflowService._register_approvers(next_node['node_instance_id'], next_node_def, application)
        
        # 現在のノードを更新
        WorkflowInstance.update_current_node(workflow_instance_id, current_node_seq + 1)
        
        return True
```

---

### 3.3 app/services/approval_service.py

```python
"""
承認処理サービス
"""
from app.models.workflow import WorkflowNodeInstance, WorkflowNodeApprover, WorkflowHistory
from app.services.workflow_service import WorkflowService


class ApprovalService:
    """承認処理サービス"""
    
    @staticmethod
    def approve(node_instance_id, approver_user_id, comment=''):
        """
        承認を実行
        
        Args:
            node_instance_id: ノードインスタンスID
            approver_user_id: 承認者ユーザーID
            comment: コメント
        
        Returns:
            bool: 成功したかどうか
        """
        # 承認権限チェック
        node_approver = WorkflowNodeApprover.get(node_instance_id, approver_user_id)
        if not node_approver:
            raise PermissionError("承認権限がありません")
        
        # ノードインスタンスを取得
        node_instance = WorkflowNodeInstance.get_by_id(node_instance_id)
        
        # ステータスチェック
        if node_instance['node_status'] != 'pending':
            raise ValueError("このノードは既に処理済みです")
        
        # ノードを承認済みに更新
        WorkflowNodeInstance.update_status(
            node_instance_id,
            'approved',
            approver_user_id,
            comment
        )
        
        # 履歴に記録
        WorkflowHistory.create(
            node_instance['workflow_instance_id'],
            node_instance_id,
            'approve',
            approver_user_id,
            comment
        )
        
        # 次のノードへ進む
        WorkflowService.advance_to_next_node(node_instance['workflow_instance_id'])
        
        return True
    
    
    @staticmethod
    def reject(node_instance_id, approver_user_id, comment):
        """
        却下を実行
        
        Args:
            node_instance_id: ノードインスタンスID
            approver_user_id: 承認者ユーザーID
            comment: 却下理由
        
        Returns:
            bool: 成功したかどうか
        """
        # 承認権限チェック
        node_approver = WorkflowNodeApprover.get(node_instance_id, approver_user_id)
        if not node_approver:
            raise PermissionError("承認権限がありません")
        
        # ノードインスタンスを取得
        node_instance = WorkflowNodeInstance.get_by_id(node_instance_id)
        
        # ステータスチェック
        if node_instance['node_status'] != 'pending':
            raise ValueError("このノードは既に処理済みです")
        
        # コメント必須チェック
        if not comment or not comment.strip():
            raise ValueError("却下理由を入力してください")
        
        # ノードを却下に更新
        WorkflowNodeInstance.update_status(
            node_instance_id,
            'rejected',
            approver_user_id,
            comment
        )
        
        # 履歴に記録
        WorkflowHistory.create(
            node_instance['workflow_instance_id'],
            node_instance_id,
            'reject',
            approver_user_id,
            comment
        )
        
        # ワークフローを却下状態に
        from app.models.workflow import WorkflowInstance
        WorkflowInstance.set_status(node_instance['workflow_instance_id'], 'rejected')
        
        # 申請を却下状態に
        from app.models.application import Application
        workflow = WorkflowInstance.get_by_id(node_instance['workflow_instance_id'])
        Application.set_status(workflow['application_id'], 'rejected')
        
        return True
    
    
    @staticmethod
    def get_pending_tasks(user_id, filters=None, page=1, per_page=20):
        """
        承認待ちタスク一覧を取得
        
        Args:
            user_id: ユーザーID
            filters: フィルタ条件
            page: ページ番号
            per_page: 1ページあたりの件数
        
        Returns:
            tuple: (タスクリスト, 総件数)
        """
        return WorkflowNodeInstance.get_pending_tasks(user_id, filters, page, per_page)
```

---

### 3.4 app/services/resource_service.py

```python
"""
リソース検索サービス
"""
from app.utils.db import get_db_connection
from app.models.master import ApplicationType


class ResourceService:
    """リソース検索サービス"""
    
    @staticmethod
    def search_resources(application_type_id, search_params):
        """
        リソースを検索
        
        Args:
            application_type_id: 申請種類ID
            search_params: 検索パラメータ
        
        Returns:
            list: 検索結果のリスト
        """
        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type or not app_type['resource_search_query']:
            raise ValueError("リソース検索がサポートされていません")
        
        # 検索SQLを実行
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = app_type['resource_search_query']
        cursor.execute(sql, search_params)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        results = []
        for row in rows:
            results.append(dict(zip([col[0].lower() for col in cursor.description], row)))
        
        return results
    
    
    @staticmethod
    def get_resource_detail(application_type_id, resource_id):
        """
        リソースの詳細を取得
        
        Args:
            application_type_id: 申請種類ID
            resource_id: リソースID
        
        Returns:
            dict: リソース詳細
        """
        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type or not app_type['resource_detail_query']:
            raise ValueError("リソース詳細取得がサポートされていません")
        
        # 詳細取得SQLを実行
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = app_type['resource_detail_query']
        cursor.execute(sql, {'resource_id': resource_id})
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return dict(zip([col[0].lower() for col in cursor.description], row))
        return None
    
    
    @staticmethod
    def validate_resource_duplication(application_type_id, field_values, exclude_resource_id=None):
        """
        リソースの重複チェック
        
        Args:
            application_type_id: 申請種類ID
            field_values: フィールド値（辞書）
            exclude_resource_id: 除外するリソースID（修正時）
        
        Returns:
            bool: 重複している場合True
        """
        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type or not app_type['resource_validation_query']:
            return False  # 重複チェックなし
        
        # 重複チェックSQLを実行
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = app_type['resource_validation_query']
        params = field_values.copy()
        params['exclude_resource_id'] = exclude_resource_id
        
        cursor.execute(sql, params)
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # duplicate_countが0より大きければ重複
        if row and row[0] > 0:
            return True
        
        return False
```

---

## 4. Routes（コントローラー層）

### 4.1 app/routes/application.py

```python
"""
申請画面のルーティング
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.application_service import ApplicationService
from app.services.resource_service import ResourceService
from app.models.master import ApplicationType
from app.utils.decorators import login_required

bp = Blueprint('application', __name__, url_prefix='/application')


@bp.route('/')
@login_required
def index():
    """申請種類選択画面"""
    application_types = ApplicationType.get_active_list()
    return render_template('application/index.html', application_types=application_types)


@bp.route('/create/<int:application_type_id>')
@login_required
def create(application_type_id):
    """新規申請作成画面"""
    # 申請種類を取得
    app_type = ApplicationType.get_by_id(application_type_id)
    if not app_type:
        flash('申請種類が見つかりません', 'error')
        return redirect(url_for('application.index'))
    
    # フィールド定義を取得
    fields = ApplicationService.get_application_form_fields(application_type_id, 'create')
    
    return render_template(
        'application/create.html',
        app_type=app_type,
        fields=fields,
        action_type='create'
    )


@bp.route('/create/<int:application_type_id>', methods=['POST'])
@login_required
def create_submit(application_type_id):
    """新規申請作成処理"""
    try:
        user_id = session.get('user_id')
        
        # フォームデータを取得
        data = {
            'application_title': request.form.get('application_title'),
            'remarks': request.form.get('remarks'),
            'details': []  # フィールドデータを構築
        }
        
        # 下書き保存か申請提出か
        if request.form.get('action') == 'draft':
            application_id = ApplicationService.create_draft(
                user_id, application_type_id, 'create', data
            )
            flash('下書きを保存しました', 'success')
            return redirect(url_for('application.detail', application_id=application_id))
        
        else:  # submit
            application_id = ApplicationService.create_draft(
                user_id, application_type_id, 'create', data
            )
            ApplicationService.submit_application(application_id, user_id)
            flash('申請を提出しました', 'success')
            return redirect(url_for('application.detail', application_id=application_id))
    
    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('application.create', application_type_id=application_type_id))


@bp.route('/modify/<int:application_type_id>')
@login_required
def modify(application_type_id):
    """修正申請画面"""
    # 申請種類を取得
    app_type = ApplicationType.get_by_id(application_type_id)
    if not app_type:
        flash('申請種類が見つかりません', 'error')
        return redirect(url_for('application.index'))
    
    return render_template(
        'application/modify.html',
        app_type=app_type,
        action_type='modify'
    )


@bp.route('/search_resource/<int:application_type_id>')
@login_required
def search_resource(application_type_id):
    """リソース検索画面"""
    # 検索パラメータを取得
    search_keyword = request.args.get('search_keyword', '')
    owner_shozoku = request.args.get('owner_shozoku', '')
    
    search_params = {
        'search_keyword': search_keyword if search_keyword else None,
        'owner_shozoku': owner_shozoku if owner_shozoku else None
    }
    
    # リソースを検索
    try:
        resources = ResourceService.search_resources(application_type_id, search_params)
        
        return render_template(
            'application/search_resource.html',
            application_type_id=application_type_id,
            resources=resources,
            search_params=search_params
        )
    
    except Exception as e:
        flash(f'検索エラー: {str(e)}', 'error')
        return redirect(url_for('application.modify', application_type_id=application_type_id))


@bp.route('/list')
@login_required
def list():
    """申請一覧"""
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # フィルタ条件
    filters = {
        'status': request.args.get('status'),
        'application_type_id': request.args.get('application_type_id', type=int)
    }
    
    # 申請一覧を取得
    from app.models.application import Application
    applications, total = Application.get_list(user_id, filters, page, per_page)
    
    # ページネーション情報
    total_pages = (total + per_page - 1) // per_page
    
    return render_template(
        'application/list.html',
        applications=applications,
        page=page,
        total_pages=total_pages,
        filters=filters
    )


@bp.route('/detail/<int:application_id>')
@login_required
def detail(application_id):
    """申請詳細"""
    from app.models.application import Application, ApplicationDetail
    
    application = Application.get_by_id(application_id)
    if not application:
        flash('申請が見つかりません', 'error')
        return redirect(url_for('application.list'))
    
    # 申請者チェック
    user_id = session.get('user_id')
    if application['applicant_user_id'] != user_id:
        flash('この申請を閲覧する権限がありません', 'error')
        return redirect(url_for('application.list'))
    
    # 詳細データを取得
    details = ApplicationDetail.get_by_application_id(application_id)
    
    return render_template(
        'application/detail.html',
        application=application,
        details=details
    )
```

---

### 4.2 app/routes/approval.py

```python
"""
承認画面のルーティング
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.services.approval_service import ApprovalService
from app.models.application import Application, ApplicationDetail
from app.utils.decorators import login_required

bp = Blueprint('approval', __name__, url_prefix='/approval')


@bp.route('/tasks')
@login_required
def task_list():
    """承認待ちタスク一覧"""
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # フィルタ条件
    filters = {
        'application_type_id': request.args.get('application_type_id', type=int)
    }
    
    # 承認待ちタスクを取得
    tasks, total = ApprovalService.get_pending_tasks(user_id, filters, page, per_page)
    
    # ページネーション情報
    total_pages = (total + per_page - 1) // per_page
    
    return render_template(
        'approval/task_list.html',
        tasks=tasks,
        page=page,
        total_pages=total_pages,
        filters=filters
    )


@bp.route('/task/<int:node_instance_id>')
@login_required
def task_detail(node_instance_id):
    """タスク詳細・承認画面"""
    user_id = session.get('user_id')
    
    # ノードインスタンスを取得
    from app.models.workflow import WorkflowNodeInstance
    node_instance = WorkflowNodeInstance.get_by_id(node_instance_id)
    
    if not node_instance:
        flash('タスクが見つかりません', 'error')
        return redirect(url_for('approval.task_list'))
    
    # 承認権限チェック
    from app.models.workflow import WorkflowNodeApprover
    node_approver = WorkflowNodeApprover.get(node_instance_id, user_id)
    if not node_approver:
        flash('このタスクを承認する権限がありません', 'error')
        return redirect(url_for('approval.task_list'))
    
    # 申請情報を取得
    from app.models.workflow import WorkflowInstance
    workflow = WorkflowInstance.get_by_id(node_instance['workflow_instance_id'])
    application = Application.get_by_id(workflow['application_id'])
    details = ApplicationDetail.get_by_application_id(application['application_id'])
    
    # ワークフロー履歴を取得
    from app.models.workflow import WorkflowHistory
    history = WorkflowHistory.get_by_workflow(workflow['workflow_instance_id'])
    
    return render_template(
        'approval/task_detail.html',
        node_instance=node_instance,
        application=application,
        details=details,
        history=history
    )


@bp.route('/approve/<int:node_instance_id>', methods=['POST'])
@login_required
def approve(node_instance_id):
    """承認実行"""
    try:
        user_id = session.get('user_id')
        comment = request.form.get('comment', '')
        
        ApprovalService.approve(node_instance_id, user_id, comment)
        
        flash('承認しました', 'success')
        return redirect(url_for('approval.task_list'))
    
    except Exception as e:
        flash(f'承認エラー: {str(e)}', 'error')
        return redirect(url_for('approval.task_detail', node_instance_id=node_instance_id))


@bp.route('/reject/<int:node_instance_id>', methods=['POST'])
@login_required
def reject(node_instance_id):
    """却下実行"""
    try:
        user_id = session.get('user_id')
        comment = request.form.get('comment', '')
        
        if not comment or not comment.strip():
            flash('却下理由を入力してください', 'error')
            return redirect(url_for('approval.task_detail', node_instance_id=node_instance_id))
        
        ApprovalService.reject(node_instance_id, user_id, comment)
        
        flash('却下しました', 'success')
        return redirect(url_for('approval.task_list'))
    
    except Exception as e:
        flash(f'却下エラー: {str(e)}', 'error')
        return redirect(url_for('approval.task_detail', node_instance_id=node_instance_id))
```

続きは次のメッセージで作成します（HTMLテンプレート構成）。
