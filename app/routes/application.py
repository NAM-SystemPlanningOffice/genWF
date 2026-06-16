"""
申請画面のルーティング
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.utils.decorators import login_required
from app.models.application_type import ApplicationType
from app.models.application_field import ApplicationField
from app.models.application import Application
from app.models.resource import Resource
from app.utils.constants import ACTION_TYPE_CREATE, ACTION_TYPE_MODIFY, ACTION_TYPE_DELETE

bp = Blueprint('application', __name__, url_prefix='/application')


@bp.route('/')
@login_required
def index():
    """申請種類選択画面"""
    try:
        # デバッグ: 環境変数を確認
        import os
        from flask import current_app
        use_mock_db = os.environ.get('USE_MOCK_DB', 'NOT_SET')
        current_app.logger.info(f"[application.index] USE_MOCK_DB = '{use_mock_db}'")

        # 管理者の場合は開発中のものも含める
        is_admin = session.get('is_admin', False)

        # 申請者の所属・ユーザーIDを取得（制限による絞り込み用）
        applicant_shozoku = session.get('shozoku')
        applicant_user_id = session.get('user_id')

        application_types = ApplicationType.get_all_active(
            include_under_development=is_admin,
            applicant_shozoku=applicant_shozoku,
            applicant_user_id=applicant_user_id
        )
        return render_template('application/index.html', application_types=application_types)
    except Exception as e:
        flash(f'申請種類の取得に失敗しました: {str(e)}', 'danger')
        import traceback
        from flask import current_app
        current_app.logger.error(f"エラー詳細:\n{traceback.format_exc()}")
        return render_template('application/index.html', application_types=[])


@bp.route('/create/<int:application_type_id>')
@login_required
def create(application_type_id):
    """新規申請作成画面"""
    from flask import current_app
    current_app.logger.info(f"[application.create] application_type_id={application_type_id}")

    try:
        # 申請種類を取得
        current_app.logger.info("[application.create] 申請種類を取得中...")
        app_type = ApplicationType.get_by_id(application_type_id)
        current_app.logger.info(f"[application.create] 申請種類取得結果: {app_type}")

        if not app_type:
            current_app.logger.warning("[application.create] 申請種類が見つかりません")
            flash('指定された申請種類が見つかりません', 'danger')
            return redirect(url_for('application.index'))

        # 新規作成をサポートしているかチェック
        if app_type.get('support_create') != 'Y':
            current_app.logger.warning("[application.create] 新規作成サポートなし")
            flash('この申請種類は新規作成をサポートしていません', 'danger')
            return redirect(url_for('application.index'))

        # 申請可能制限チェック
        applicant_shozoku = session.get('shozoku')
        applicant_user_id = session.get('user_id')
        if not ApplicationType.is_allowed_to_apply(app_type, applicant_shozoku, applicant_user_id):
            current_app.logger.warning(f"[application.create] 制限により申請不可: user_id={applicant_user_id}, shozoku={applicant_shozoku}")
            flash('この申請種類はあなたは申請できません', 'danger')
            return redirect(url_for('application.index'))

        # 申請フィールドを取得
        current_app.logger.info("[application.create] フィールドを取得中...")
        fields = ApplicationField.get_by_application_type(application_type_id)
        current_app.logger.info(f"[application.create] フィールド取得結果: {len(fields)}件")

        # プルダウンの選択肢とバリデーションルールを取得
        from app.models.admin.field_validation import FieldValidation

        # 動的プルダウン用のバインド変数を準備
        applicant_user_id = session.get('user_id')
        applicant_shozoku = session.get('shozoku')
        dynamic_params = {
            'applicant_user_id': applicant_user_id,
            'applicant_shozoku': applicant_shozoku,
            'resource_id': None  # 新規作成時はresource_idはない
        }

        for field in fields:
            # プルダウン選択肢（select と datalist 両方に対応）
            if field['field_type'] in ('select', 'datalist') and field.get('pulldown_group_id'):
                if field.get('pulldown_is_dynamic') == 'Y':
                    # 動的プルダウン
                    query = field.get('pulldown_dynamic_query')
                    if query:
                        field['options'] = ApplicationField.get_dynamic_pulldown_options(query, dynamic_params)
                else:
                    # 静的プルダウン
                    field['options'] = ApplicationField.get_pulldown_options(field['pulldown_group_id'])

            # バリデーションルール（新規作成用）
            validations = FieldValidation.get_by_field(field['field_id'])
            field['validations'] = [v for v in validations if v.get('apply_on_create') == 'Y']

        current_app.logger.info("[application.create] テンプレートをレンダリング...")
        return render_template('application/create.html',
                               app_type=app_type,
                               fields=fields,
                               action_type=ACTION_TYPE_CREATE)
    except Exception as e:
        current_app.logger.error(f'[application.create] エラー: {str(e)}')
        import traceback
        current_app.logger.error(f"[application.create] トレース:\n{traceback.format_exc()}")
        flash(f'申請作成画面の表示に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.index'))


@bp.route('/modify/<int:application_type_id>')
@login_required
def modify(application_type_id):
    """既存設定の修正申請画面（リソース検索）"""
    try:
        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type:
            flash('指定された申請種類が見つかりません', 'danger')
            return redirect(url_for('application.index'))

        # 修正をサポートしているかチェック（複数レコード入力の場合は個別レコード単位でチェックするのでスキップ）
        if app_type.get('support_modify') != 'Y' and app_type.get('is_multi_record') != 'Y':
            flash('この申請種類は修正をサポートしていません', 'danger')
            return redirect(url_for('application.index'))

        # リソース検索クエリがあるか確認
        search_query = app_type.get('resource_search_query')
        if not search_query:
            flash('この申請種類はリソース検索をサポートしていません', 'danger')
            return redirect(url_for('application.index'))

        # 検索キーワードを取得
        search_keyword = request.args.get('search_keyword', '').strip()
        user_id = session.get('user_id')
        applicant_shozoku = session.get('shozoku')

        # リソース検索（キーワードが空の場合は全件検索）
        resources = None
        # GETパラメータが存在する場合のみ検索実行（初回表示では検索しない）
        if 'search_keyword' in request.args:
            keyword_param = f'%{search_keyword}%' if search_keyword else '%%'
            resources = Resource.search_resources(search_query, {
                'search_keyword': keyword_param,
                'applicant_user_id': user_id,
                'applicant_shozoku': applicant_shozoku
            })

        return render_template('application/search_resource.html',
                               app_type=app_type,
                               resources=resources,
                               search_keyword=search_keyword,
                               action_type=ACTION_TYPE_MODIFY)
    except Exception as e:
        flash(f'修正申請画面の表示に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.index'))


@bp.route('/delete/<int:application_type_id>')
@login_required
def delete(application_type_id):
    """既存設定の削除申請画面（リソース検索）"""
    try:
        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type:
            flash('指定された申請種類が見つかりません', 'danger')
            return redirect(url_for('application.index'))

        # 削除をサポートしているかチェック
        if app_type.get('support_delete') != 'Y':
            flash('この申請種類は削除をサポートしていません', 'danger')
            return redirect(url_for('application.index'))

        # リソース検索クエリがあるか確認
        search_query = app_type.get('resource_search_query')
        if not search_query:
            flash('この申請種類はリソース検索をサポートしていません', 'danger')
            return redirect(url_for('application.index'))

        # 検索キーワードを取得
        search_keyword = request.args.get('search_keyword', '').strip()
        user_id = session.get('user_id')
        applicant_shozoku = session.get('shozoku')

        # リソース検索（キーワードが空の場合は全件検索）
        resources = None
        # GETパラメータが存在する場合のみ検索実行（初回表示では検索しない）
        if 'search_keyword' in request.args:
            keyword_param = f'%{search_keyword}%' if search_keyword else '%%'
            resources = Resource.search_resources(search_query, {
                'search_keyword': keyword_param,
                'applicant_user_id': user_id,
                'applicant_shozoku': applicant_shozoku
            })

        return render_template('application/search_resource.html',
                               app_type=app_type,
                               resources=resources,
                               search_keyword=search_keyword,
                               action_type=ACTION_TYPE_DELETE)
    except Exception as e:
        flash(f'削除申請画面の表示に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.index'))


@bp.route('/modify/<int:application_type_id>/<path:resource_id>')
@login_required
def modify_with_resource(application_type_id, resource_id):
    """既存リソースの修正申請画面"""
    from flask import current_app
    try:
        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type:
            flash('指定された申請種類が見つかりません', 'danger')
            return redirect(url_for('application.index'))

        # リソース詳細を取得
        detail_query = app_type.get('resource_detail_query')
        resource = Resource.get_resource_detail(detail_query, resource_id)

        # 申請フィールドを取得
        fields = ApplicationField.get_by_application_type(application_type_id)

        # プルダウンの選択肢とバリデーションルールを取得
        from app.models.admin.field_validation import FieldValidation

        # 動的プルダウン用のバインド変数を準備
        applicant_user_id = session.get('user_id')
        applicant_shozoku = session.get('shozoku')
        dynamic_params = {
            'applicant_user_id': applicant_user_id,
            'applicant_shozoku': applicant_shozoku,
            'resource_id': resource_id
        }

        for field in fields:
            # プルダウン選択肢（select と datalist 両方に対応）
            if field['field_type'] in ('select', 'datalist') and field.get('pulldown_group_id'):
                if field.get('pulldown_is_dynamic') == 'Y':
                    query = field.get('pulldown_dynamic_query')
                    if query:
                        field['options'] = ApplicationField.get_dynamic_pulldown_options(query, dynamic_params)
                else:
                    field['options'] = ApplicationField.get_pulldown_options(field['pulldown_group_id'])

            # バリデーションルール（修正用）
            validations = FieldValidation.get_by_field(field['field_id'])
            field['validations'] = [v for v in validations if v.get('apply_on_modify') == 'Y']

            # resource_column_nameに対応する既存値をセット
            if resource and field.get('resource_column_name'):
                column_name = field['resource_column_name']
                if column_name in resource:
                    field['current_value'] = resource[column_name]

                # resource_label_columnがある場合はlabelもセット
                label_column_name = field.get('resource_label_column')
                if label_column_name and label_column_name in resource:
                    field['current_label'] = resource[label_column_name]
                else:
                    # labelカラムが未指定の場合はvalueと同じ
                    field['current_label'] = field.get('current_value')

        from datetime import date
        return render_template('application/create.html',
                               app_type=app_type,
                               fields=fields,
                               action_type=ACTION_TYPE_MODIFY,
                               resource=resource,
                               resource_id=resource_id,
                               today=date.today().isoformat())
    except Exception as e:
        current_app.logger.error(f'修正申請画面エラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'修正申請画面の表示に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.modify', application_type_id=application_type_id))


@bp.route('/delete/<int:application_type_id>/<path:resource_id>')
@login_required
def delete_with_resource(application_type_id, resource_id):
    """既存リソースの削除申請画面"""
    try:
        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type:
            flash('指定された申請種類が見つかりません', 'danger')
            return redirect(url_for('application.index'))

        # リソース詳細を取得
        detail_query = app_type.get('resource_detail_query')
        resource = Resource.get_resource_detail(detail_query, resource_id)

        # 申請フィールドを取得
        fields = ApplicationField.get_by_application_type(application_type_id)

        return render_template('application/create.html',
                               app_type=app_type,
                               fields=fields,
                               action_type=ACTION_TYPE_DELETE,
                               resource=resource,
                               resource_id=resource_id)
    except Exception as e:
        flash(f'削除申請画面の表示に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.delete', application_type_id=application_type_id))


@bp.route('/create/<int:application_type_id>/submit', methods=['POST'])
@login_required
def submit_create(application_type_id):
    """新規申請の提出処理"""
    from flask import current_app
    from app.services.validation_service import ValidationService
    try:
        user_id = session.get('user_id')
        applicant_shozoku = session.get('shozoku')

        if not applicant_shozoku:
            flash('所属が選択されていません。再度ログインしてください。', 'danger')
            return redirect(url_for('auth.login'))

        action = request.form.get('action')  # save_draft or submit
        current_app.logger.info(f"[submit_create] action={action}, user_id={user_id}, shozoku={applicant_shozoku}")

        # 開発中フラグのチェック（管理者以外が提出する場合）
        if action == 'submit':
            is_admin = session.get('is_admin', False)
            if not is_admin:
                app_type = ApplicationType.get_by_id(application_type_id)
                if app_type and app_type.get('is_under_development') == 'Y':
                    flash('この申請種類は現在開発中のため、提出できません。下書き保存のみ可能です。', 'danger')
                    return redirect(url_for('application.create', application_type_id=application_type_id))

        # まず下書きとして保存（バリデーションエラー時に入力値を保持するため）
        application_data = {
            'application_type_id': application_type_id,
            'action_type': ACTION_TYPE_CREATE,
            'applicant_user_id': user_id,
            'applicant_shozoku': applicant_shozoku,
            'application_title': request.form.get('application_title'),
            'remarks': request.form.get('remarks')
        }

        # 申請を作成
        application_id = Application.create(application_data)

        # フィールド値を保存
        from app.models.application_detail import ApplicationDetail
        field_values = []
        field_labels = {}  # field_id -> label のマッピング

        # まずlabelを収集
        for key, value in request.form.items():
            if key.startswith('field_') and key.endswith('_label'):
                field_id = int(key.replace('field_', '').replace('_label', ''))
                field_labels[field_id] = value

        # field_valueとfield_labelを組み合わせて保存
        for key, value in request.form.items():
            if key.startswith('field_') and not key.endswith('_label'):
                field_id = int(key.replace('field_', ''))
                field_values.append({
                    'detail_seq': 1,
                    'field_id': field_id,
                    'field_value': value,
                    'field_label': field_labels.get(field_id)
                })

        if field_values:
            ApplicationDetail.save_details(application_id, field_values)

        # バリデーション実行（申請提出時のみ）
        if action == 'submit':
            validation_errors = []
            fields = ApplicationField.get_by_application_type(application_type_id)

            # リソースIDを取得（リソース選択型の申請種類の場合）
            validation_resource_id = None
            for field in fields:
                if field.get('field_code') == 'resource_id':
                    validation_resource_id = request.form.get(f"field_{field['field_id']}")
                    break

            # 全フィールドの値を収集（クロスフィールドバリデーション用）
            all_field_values = {}
            for field in fields:
                field_key = f"field_{field['field_id']}"
                field_value = request.form.get(field_key)
                all_field_values[field['field_id']] = field_value

            # 各フィールドのバリデーション実行
            for field in fields:
                field_key = f"field_{field['field_id']}"
                field_value = request.form.get(field_key)

                # バリデーション実行（新規作成モード）
                is_valid, errors = ValidationService.validate_field(
                    field_id=field['field_id'],
                    value=field_value,
                    operation_type='create',
                    resource_id=validation_resource_id,
                    all_field_values=all_field_values
                )

                if not is_valid:
                    for error in errors:
                        validation_errors.append(f"{field['field_name']}: {error}")

            # バリデーションエラーがある場合は下書き編集画面へ
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'danger')
                return redirect(url_for('application.edit', application_id=application_id))

            # バリデーションが通った場合は承認者選択画面へ
            return redirect(url_for('application.select_approvers', application_id=application_id))
        else:
            # 下書き保存のみの場合
            flash(f'下書きとして保存しました（申請ID: {application_id}）', 'success')
            return redirect(url_for('application.list'))

    except Exception as e:
        current_app.logger.error(f'申請の提出に失敗: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'申請の提出に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.create', application_type_id=application_type_id))


@bp.route('/detail/<int:application_id>')
@login_required
def detail(application_id):
    """申請詳細画面"""
    try:
        user_id = session.get('user_id')

        # 申請情報を取得
        application = Application.get_by_id(application_id)
        if not application:
            flash('指定された申請が見つかりません', 'danger')
            return redirect(url_for('application.list'))

        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application['application_type_id'])

        # 申請詳細を取得
        from app.models.application_detail import ApplicationDetail
        details = ApplicationDetail.get_by_application(application_id)

        # 複数レコード申請の場合、detail_seqでグループ化（非表示フィールドは除外）
        is_multi_record = app_type and app_type.get('is_multi_record') == 'Y'
        records_by_seq = {}
        if is_multi_record and details:
            for detail in details:
                # 非表示フィールドは除外
                if detail.get('is_visible') != 'Y':
                    continue

                # detail_actionがNone、'none'、'readonly'のレコードは除外
                detail_action = detail.get('detail_action')
                if detail_action is None or detail_action in ('none', 'readonly'):
                    continue

                seq = detail['detail_seq']
                if seq not in records_by_seq:
                    records_by_seq[seq] = {
                        'action': detail.get('detail_action', 'add'),
                        'fields': []
                    }
                records_by_seq[seq]['fields'].append(detail)

        # ワークフロー情報を取得
        from app.models.workflow import WorkflowInstance, WorkflowNodeInstance
        from app.models.approval_task import ApprovalTask
        from flask import current_app
        workflow_nodes = []
        can_withdraw = False  # 取り下げ可能フラグの初期化
        workflow_instance = WorkflowInstance.get_by_application(application_id)
        current_app.logger.info(f'[detail] app_id={application_id}, workflow_instance={workflow_instance is not None}')
        if workflow_instance:
            workflow_nodes = WorkflowNodeInstance.get_by_workflow(
                workflow_instance['workflow_instance_id']
            )
            current_app.logger.info(f'[detail] app_id={application_id}, workflow_nodes count={len(workflow_nodes)}')

            # 取り下げ可能かチェック（申請者本人で、スキップされていない最初のノードがpendingの場合のみ）
            can_withdraw = False
            if application['applicant_user_id'] == user_id and application['application_status'] == 'submitted':
                # スキップされていない最初のノードを探す
                first_non_skipped_node = None
                for node in workflow_nodes:
                    if node['node_status'] != 'skipped':
                        first_non_skipped_node = node
                        break

                if first_non_skipped_node:
                    first_node_status = first_non_skipped_node['node_status']
                    current_app.logger.info(f'[detail] can_withdraw check: first_non_skipped_node seq={first_non_skipped_node["node_seq"]}, status={first_node_status}')
                    # 最初のノードがpendingの場合のみ取り下げ可能
                    can_withdraw = (first_node_status == 'pending')
                    current_app.logger.info(f'[detail] can_withdraw={can_withdraw}')
                else:
                    current_app.logger.info(f'[detail] can_withdraw check: no non-skipped node found')

            # 各ノードについて、引き戻し可能かチェックと承認者情報の追加
            for i, node in enumerate(workflow_nodes):
                node['can_recall'] = False

                # 承認待ち中または承認済みのノードで、自分が承認者の場合
                if node['node_status'] in ('pending', 'approved'):
                    # このノードの承認者リストを取得
                    approvers = ApprovalTask.get_approvers_for_node(node['node_instance_id'])
                    current_app.logger.info(f'[detail] node_id={node["node_instance_id"]}, node_status={node["node_status"]}, approvers={len(approvers)}')

                    # 承認者候補をノード情報に追加（pendingの場合に表示用）
                    node['approvers'] = approvers

                    # 自分が実際に承認したか確認（approval_status='approved'）
                    my_approval = next((a for a in approvers if a['approver_user_id'] == user_id and a.get('approval_status') == 'approved'), None)
                    current_app.logger.info(f'[detail] node_id={node["node_instance_id"]}, user={user_id}, my_approval={my_approval is not None}')

                    # 自分が承認した場合のみ引き戻し可能
                    if my_approval:
                        # 現在のノード、または次のノードが未処理かチェック
                        # （自分が承認済みでもノードがまだpendingの場合も引き戻し可能）
                        can_recall_this_node = (node['node_status'] == 'pending')

                        # ノードが完了している場合は、次のノードが未処理かチェック
                        next_node_unprocessed = False
                        if node['node_status'] == 'approved':
                            for j in range(i + 1, len(workflow_nodes)):
                                next_node = workflow_nodes[j]
                                if next_node['node_status'] != 'skipped':
                                    if next_node['node_status'] in ('pending', 'waiting'):
                                        next_node_unprocessed = True
                                    break

                        node['can_recall'] = can_recall_this_node or next_node_unprocessed
                        current_app.logger.info(f'[detail] node_id={node["node_instance_id"]}, can_recall_this={can_recall_this_node}, next_unprocessed={next_node_unprocessed}, can_recall={node["can_recall"]}')

        return render_template('application/detail.html',
                               application=application,
                               app_type=app_type,
                               details=details,
                               is_multi_record=is_multi_record,
                               records_by_seq=records_by_seq,
                               workflow_nodes=workflow_nodes,
                               can_withdraw=can_withdraw)
    except Exception as e:
        flash(f'申請詳細の取得に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.list'))


@bp.route('/withdraw/<int:application_id>', methods=['POST'])
@login_required
def withdraw(application_id):
    """申請の取り下げ"""
    from flask import current_app
    try:
        user_id = session.get('user_id')

        # 申請を取得
        application = Application.get_by_id(application_id)
        if not application:
            flash('指定された申請が見つかりません', 'danger')
            return redirect(url_for('application.list'))

        # 申請者本人かチェック
        if application['applicant_user_id'] != user_id:
            flash('他人の申請は取り下げできません', 'danger')
            return redirect(url_for('application.detail', application_id=application_id))

        # ステータスが submitted かチェック
        if application['application_status'] != 'submitted':
            flash('提出済みの申請のみ取り下げできます', 'danger')
            return redirect(url_for('application.detail', application_id=application_id))

        # ワークフローインスタンスを取得
        from app.models.workflow import WorkflowInstance
        workflow = WorkflowInstance.get_by_application(application_id)

        if workflow and workflow['workflow_status'] == 'in_progress':
            # ワークフローを withdrawn に更新（ノードも withdrawn に更新）
            WorkflowInstance.withdraw(workflow['workflow_instance_id'])

        # 申請ステータスを draft（下書き）に戻す
        # これにより修正して再提出、または削除が可能になる
        Application.update_status(application_id, 'draft')

        flash('申請を取り下げて下書き状態に戻しました。修正して再提出、または削除できます。', 'success')
        return redirect(url_for('application.list'))

    except Exception as e:
        current_app.logger.error(f'申請取り下げエラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'申請の取り下げに失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.detail', application_id=application_id))


@bp.route('/list')
@login_required
def list():
    """統合タスク一覧（申請一覧 + 承認タスク）"""
    from flask import current_app
    try:
        user_id = session.get('user_id')
        if not user_id:
            flash('ログインが必要です', 'danger')
            return redirect(url_for('auth.login'))

        # 統合タスク一覧を取得
        tasks = Application.get_integrated_task_list(user_id)

        # 各タスクに対してアクションとユーザー視点のステータスを判定
        from app.models.approval_task import ApprovalTask
        from app.models.workflow import WorkflowInstance, WorkflowNodeInstance
        from app.utils.db import get_db_connection, dict_factory

        filtered_tasks = []

        for task in tasks:
            task['actions'] = []
            task['user_status'] = None  # ユーザー視点のステータス
            should_display = True

            is_applicant = (task['applicant_user_id'] == user_id)
            has_pending_task = (task.get('pending_task_count', 0) > 0)

            # 承認待ちタスクがある場合（最優先）
            if has_pending_task:
                task['user_status'] = 'pending_approval'
                task['actions'].append('approve')

            # 申請者視点のステータス（承認待ちタスクがない場合）
            elif is_applicant:
                if task['application_status'] == 'draft':
                    task['user_status'] = 'draft'
                    task['actions'].extend(['edit', 'delete'])
                elif task['application_status'] == 'submitted':
                    task['user_status'] = 'submitted'
                elif task['application_status'] == 'approved':
                    task['user_status'] = 'approved'
                elif task['application_status'] == 'rejected':
                    task['user_status'] = 'rejected'

            # 承認者視点のステータスとフィルタリング（承認待ちタスクがない、かつ申請者でない場合）
            elif not is_applicant:
                # 最新のワークフローインスタンスを取得
                workflow_instance = WorkflowInstance.get_by_application(task['application_id'])

                if workflow_instance and workflow_instance['workflow_status'] == 'in_progress':
                    # 自分の全承認ノードを取得
                    conn = get_db_connection()
                    cursor = conn.cursor()

                    sql = """
                        SELECT ni.node_instance_id, ni.node_seq, ni.node_status, na.approval_status
                        FROM T_WORKFLOW_NODE_INSTANCE ni
                        INNER JOIN T_WORKFLOW_NODE_APPROVER na ON ni.node_instance_id = na.node_instance_id
                        WHERE ni.workflow_instance_id = :workflow_instance_id
                          AND na.approver_user_id = :user_id
                        ORDER BY ni.node_seq
                    """
                    cursor.execute(sql, {
                        'workflow_instance_id': workflow_instance['workflow_instance_id'],
                        'user_id': user_id
                    })
                    my_nodes = dict_factory(cursor)
                    cursor.close()

                    if my_nodes:
                        current_node_seq = workflow_instance['current_node_seq']
                        current_app.logger.info(f'[list] app_id={task["application_id"]}, my_nodes count={len(my_nodes)}, current_seq={current_node_seq}')

                        # 自分の承認済みノードを探す（node_seqが小さい順）
                        my_approved_node = None
                        for node in my_nodes:
                            if node['approval_status'] == 'approved':
                                my_approved_node = node
                                break

                        # まだ承認していないpendingノードがあるかチェック
                        has_pending = any(n['node_status'] == 'pending' and n['approval_status'] == 'pending' for n in my_nodes)

                        if has_pending:
                            # 自分が承認待ち（個別ステータスも確認）
                            task['user_status'] = 'pending_approval'
                            task['actions'].append('approve')
                            current_app.logger.info(f'[list] app_id={task["application_id"]} -> pending_approval')
                        elif my_approved_node:
                            # 自分が承認済みの場合、次のノードが未処理なら引き戻し可能
                            # 全ノードを取得して判定
                            cursor = conn.cursor()
                            sql_all_nodes = """
                                SELECT node_instance_id, node_seq, node_status
                                FROM T_WORKFLOW_NODE_INSTANCE
                                WHERE workflow_instance_id = :workflow_instance_id
                                ORDER BY node_seq
                            """
                            cursor.execute(sql_all_nodes, {'workflow_instance_id': workflow_instance['workflow_instance_id']})
                            all_nodes = dict_factory(cursor)
                            cursor.close()

                            # 自分が承認したノードより後で、スキップされていない最初のノードを探す
                            next_node_unprocessed = False
                            for node in all_nodes:
                                if node['node_seq'] > my_approved_node['node_seq'] and node['node_status'] != 'skipped':
                                    if node['node_status'] in ('pending', 'waiting'):
                                        next_node_unprocessed = True
                                    break

                            if next_node_unprocessed:
                                task['user_status'] = 'approved_by_me'
                                task['actions'].append('recall')
                                current_app.logger.info(f'[list] app_id={task["application_id"]} -> approved_by_me (recall)')
                            else:
                                # 次のノードが既に処理済み → 非表示
                                should_display = False
                                current_app.logger.info(f'[list] app_id={task["application_id"]} -> hidden (next node processed)')
                        else:
                            # completed_by_peerの可能性
                            has_completed_by_peer = any(n['approval_status'] == 'completed_by_peer' for n in my_nodes)
                            if has_completed_by_peer:
                                task['user_status'] = 'completed_by_peer'
                                current_app.logger.info(f'[list] app_id={task["application_id"]} -> completed_by_peer')
                                # アクションなし（表示のみ）
                            else:
                                # それ以外 → 非表示
                                should_display = False
                                current_app.logger.info(f'[list] app_id={task["application_id"]} -> hidden (other status)')
                    else:
                        should_display = False
                elif task['application_status'] in ('approved', 'rejected'):
                    # 完了済み（1週間以内）は表示
                    task['user_status'] = task['application_status']
                else:
                    should_display = False

            if should_display:
                filtered_tasks.append(task)

        return render_template('application/integrated_list.html', tasks=filtered_tasks)
    except Exception as e:
        current_app.logger.error(f'タスク一覧取得エラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'タスク一覧の取得に失敗しました: {str(e)}', 'danger')
        return render_template('application/integrated_list.html', tasks=[])


@bp.route('/edit/<int:application_id>')
@login_required
def edit(application_id):
    """下書き申請の編集画面"""
    from flask import current_app
    try:
        user_id = session.get('user_id')

        # 申請情報を取得
        application = Application.get_by_id(application_id)
        if not application:
            flash('指定された申請が見つかりません', 'danger')
            return redirect(url_for('application.list'))

        # 権限チェック：申請者本人のみ
        if application['applicant_user_id'] != user_id:
            flash('この申請を編集する権限がありません', 'danger')
            return redirect(url_for('application.list'))

        # ステータスチェック：下書きのみ編集可能
        if application['application_status'] != 'draft':
            flash('下書き状態の申請のみ編集できます', 'danger')
            return redirect(url_for('application.detail', application_id=application_id))

        # 申請種類を取得
        application_type = ApplicationType.get_by_id(application['application_type_id'])
        if not application_type:
            flash('申請種類が見つかりません', 'danger')
            return redirect(url_for('application.list'))

        # 申請可能制限チェック（申請者本人が既に作成した申請の場合はスキップ）
        # 編集時は申請者本人であることが既に確認済み（673行目）なのでチェック不要
        # （一度申請できた内容は、編集時も継続して編集可能とする）

        # 複数レコード形式の場合は専用の編集画面へリダイレクト
        if application_type.get('is_multi_record') == 'Y':
            resource_id = application.get('resource_id')
            if not resource_id:
                flash('リソースIDが見つかりません', 'danger')
                return redirect(url_for('application.list'))
            # 複数レコード編集画面へ（application_idを渡す）
            return redirect(url_for('application_multi.edit_multi_record',
                                    application_id=application_id,
                                    application_type_id=application['application_type_id'],
                                    resource_id=resource_id))

        # フィールド定義を取得
        fields = ApplicationField.get_by_application_type(application['application_type_id'])

        # 動的プルダウン用のバインド変数を準備
        applicant_user_id = session.get('user_id')
        applicant_shozoku = session.get('shozoku')
        resource_id = application.get('resource_id')
        dynamic_params = {
            'applicant_user_id': applicant_user_id,
            'applicant_shozoku': applicant_shozoku,
            'resource_id': resource_id
        }

        # プルダウンの選択肢とバリデーションルールを取得
        for field in fields:
            if field['field_type'] in ('select', 'datalist') and field.get('pulldown_group_id'):
                if field.get('pulldown_is_dynamic') == 'Y':
                    # 動的プルダウン
                    query = field.get('pulldown_dynamic_query')
                    if query:
                        field['options'] = ApplicationField.get_dynamic_pulldown_options(query, dynamic_params)
                else:
                    # 静的プルダウン
                    field['options'] = ApplicationField.get_pulldown_options(field['pulldown_group_id'])

            # バリデーションルールを取得
            from app.models.admin.field_validation import FieldValidation
            validations = FieldValidation.get_by_field(field['field_id'])
            if validations:
                field['validations'] = validations

        # 申請詳細（既存の入力値）を取得
        from app.models.application_detail import ApplicationDetail
        details = ApplicationDetail.get_by_application(application_id)

        # フィールドごとの値を辞書化
        field_values = {}
        for detail in details:
            field_values[detail['field_code']] = detail['field_value']

        return render_template('application/edit.html',
                             application=application,
                             application_type=application_type,
                             action_type=application.get('action_type'),
                             fields=fields,
                             field_values=field_values)

    except Exception as e:
        current_app.logger.error(f'申請編集画面表示エラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'編集画面の表示に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.list'))


@bp.route('/edit/<int:application_id>/submit', methods=['POST'])
@login_required
def submit_edit(application_id):
    """下書き申請の更新処理"""
    from flask import current_app
    try:
        user_id = session.get('user_id')
        applicant_shozoku = session.get('shozoku')

        if not applicant_shozoku:
            flash('所属が選択されていません。再度ログインしてください。', 'danger')
            return redirect(url_for('auth.login'))

        # 申請情報を取得
        application = Application.get_by_id(application_id)
        if not application:
            flash('指定された申請が見つかりません', 'danger')
            return redirect(url_for('application.list'))

        # 権限チェック
        if application['applicant_user_id'] != user_id:
            flash('この申請を編集する権限がありません', 'danger')
            return redirect(url_for('application.list'))

        # ステータスチェック
        if application['application_status'] != 'draft':
            flash('下書き状態の申請のみ編集できます', 'danger')
            return redirect(url_for('application.detail', application_id=application_id))

        action = request.form.get('action')  # save_draft or submit

        # バリデーション実行（申請提出時のみ）
        if action == 'submit':
            from app.services.validation_service import ValidationService
            validation_errors = []
            fields = ApplicationField.get_by_application_type(application['application_type_id'])

            # 操作タイプとresource_idを決定
            action_type = application.get('action_type')
            resource_id = application.get('resource_id')
            if action_type == 'modify' and resource_id:
                # 修正申請の場合は、自分自身を除外してチェック
                operation_type = 'modify'
            else:
                # 新規作成申請の場合
                operation_type = 'create'
                # リソースIDをフォームから取得（リソース選択型の申請種類の場合）
                if not resource_id:
                    for field in fields:
                        if field.get('field_code') == 'resource_id':
                            resource_id = request.form.get(f"field_{field['field_id']}")
                            break

            # 全フィールドの値を収集（クロスフィールドバリデーション用）
            all_field_values = {}
            for field in fields:
                field_key = f"field_{field['field_id']}"
                field_value = request.form.get(field_key)
                all_field_values[field['field_id']] = field_value

            # 各フィールドのバリデーション実行
            for field in fields:
                field_key = f"field_{field['field_id']}"
                field_value = request.form.get(field_key)

                # バリデーション実行
                is_valid, errors = ValidationService.validate_field(
                    field_id=field['field_id'],
                    value=field_value,
                    operation_type=operation_type,
                    resource_id=resource_id,
                    all_field_values=all_field_values
                )

                if not is_valid:
                    for error in errors:
                        validation_errors.append(f"{field['field_name']}: {error}")

            # バリデーションエラーがある場合は戻る
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'danger')
                return redirect(url_for('application.edit', application_id=application_id))

        # 申請基本情報を更新
        application_data = {
            'application_title': request.form.get('application_title'),
            'remarks': request.form.get('remarks')
        }
        Application.update(application_id, application_data)

        # 申請詳細を更新（既存データを削除して再登録）
        from app.models.application_detail import ApplicationDetail
        ApplicationDetail.delete_by_application(application_id)

        fields = ApplicationField.get_by_application_type(application['application_type_id'])

        # フィールド値を収集
        field_values = []
        for field in fields:
            field_id = field['field_id']
            field_value = request.form.get(f"field_{field_id}")
            field_label = request.form.get(f"field_{field_id}_label")
            if field_value:
                field_values.append({
                    'detail_seq': 1,
                    'field_id': field_id,
                    'field_value': field_value,
                    'field_label': field_label
                })

        # 申請詳細を保存
        if field_values:
            ApplicationDetail.save_details(application_id, field_values)

        # ステータス更新
        current_app.logger.info(f'[submit_edit] action={action}, application_id={application_id}')
        if action == 'submit':
            # 承認者選択画面へリダイレクト（select_approvers内でワークフロー開始判定を行う）
            current_app.logger.info(f'[submit_edit] 承認者選択画面へリダイレクト')
            return redirect(url_for('application.select_approvers', application_id=application_id))
        else:
            flash(f'下書きを更新しました（申請ID: {application_id}）', 'success')
            return redirect(url_for('application.list'))

    except Exception as e:
        current_app.logger.error(f'申請更新エラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'申請の更新に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.edit', application_id=application_id))


@bp.route('/delete-draft/<int:application_id>')
@login_required
def delete_draft(application_id):
    """下書き申請の削除"""
    from flask import current_app
    try:
        user_id = session.get('user_id')

        # 申請情報を取得
        application = Application.get_by_id(application_id)
        if not application:
            flash('指定された申請が見つかりません', 'danger')
            return redirect(url_for('application.list'))

        # 権限チェック
        if application['applicant_user_id'] != user_id:
            flash('この申請を削除する権限がありません', 'danger')
            return redirect(url_for('application.list'))

        # ステータスチェック
        if application['application_status'] != 'draft':
            flash('下書き状態の申請のみ削除できます', 'danger')
            return redirect(url_for('application.detail', application_id=application_id))

        # 申請を削除（CASCADE で詳細も削除される）
        Application.delete(application_id)

        flash('下書きを削除しました', 'success')
        return redirect(url_for('application.list'))

    except Exception as e:
        current_app.logger.error(f'申請削除エラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'申請の削除に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.list'))


@bp.route('/recall-node/<int:node_instance_id>', methods=['POST'])
@login_required
def recall_node(node_instance_id):
    """承認済みノードの引き戻し"""
    from flask import current_app
    try:
        user_id = session.get('user_id')

        # 引き戻し処理
        from app.services.workflow_service import WorkflowService
        WorkflowService.recall_node(node_instance_id, user_id)

        # 申請IDを取得してリダイレクト
        from app.utils.db import get_db_connection, dict_fetchone
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT wi.application_id
            FROM T_WORKFLOW_NODE_INSTANCE ni
            INNER JOIN T_WORKFLOW_INSTANCE wi ON ni.workflow_instance_id = wi.workflow_instance_id
            WHERE ni.node_instance_id = :node_instance_id
        """
        cursor.execute(sql, {'node_instance_id': node_instance_id})
        result = dict_fetchone(cursor)
        cursor.close()

        if result:
            application_id = result['application_id']
            flash('承認を引き戻しました。再度承認または差し戻しを行ってください。', 'success')
            return redirect(url_for('application.detail', application_id=application_id))
        else:
            flash('申請が見つかりません', 'danger')
            return redirect(url_for('application.list'))

    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('application.list'))
    except Exception as e:
        current_app.logger.error(f'引き戻しエラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'引き戻し処理に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.list'))


@bp.route('/select_approvers/<int:application_id>')
@login_required
def select_approvers(application_id):
    """承認者選択画面"""
    from flask import current_app
    try:
        user_id = session.get('user_id')

        # 申請情報を取得
        application = Application.get_by_id(application_id)
        if not application:
            flash('指定された申請が見つかりません', 'danger')
            return redirect(url_for('application.list'))

        # 申請者本人かチェック
        if application['applicant_user_id'] != user_id:
            flash('他人の申請に対して承認者を選択できません', 'danger')
            return redirect(url_for('application.detail', application_id=application_id))

        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application['application_type_id'])
        if not app_type:
            flash('申請種類が見つかりません', 'danger')
            return redirect(url_for('application.list'))

        # ワークフロー定義を取得して承認者を予め取得
        from app.models.workflow import WorkflowDefinition
        from app.models.user import User
        from app.utils.constants import NODE_TYPE_APPLICANT_DEPT, NODE_TYPE_JURISDICTION_DEPT

        workflow_definition_id = app_type['workflow_definition_id']
        node_definitions = WorkflowDefinition.get_nodes(workflow_definition_id)

        # 申請者所属の承認者を取得
        applicant_dept_approvers = []
        jurisdiction_dept_approvers = []

        for node_def in node_definitions:
            node_type = node_def['node_type']

            if node_type == NODE_TYPE_APPLICANT_DEPT:
                applicant_shozoku = application.get('applicant_shozoku')
                current_app.logger.info(f'[select_approvers] app_id={application_id}, applicant_dept node found, shozoku={applicant_shozoku}')
                if applicant_shozoku:
                    applicant_dept_approvers = User.get_approvers_by_shozoku(applicant_shozoku)
                    current_app.logger.info(f'[select_approvers] app_id={application_id}, applicant_dept_approvers count={len(applicant_dept_approvers)}')

            elif node_type == NODE_TYPE_JURISDICTION_DEPT:
                jurisdiction_shozoku = application.get('jurisdiction_shozoku')
                # スキップ判定
                applicant_shozoku = application.get('applicant_shozoku')
                current_app.logger.info(f'[select_approvers] app_id={application_id}, jurisdiction_dept node found, jurisdiction={jurisdiction_shozoku}, applicant={applicant_shozoku}')
                if jurisdiction_shozoku and jurisdiction_shozoku != applicant_shozoku:
                    jurisdiction_dept_approvers = User.get_approvers_by_shozoku(jurisdiction_shozoku)
                    current_app.logger.info(f'[select_approvers] app_id={application_id}, jurisdiction_dept_approvers count={len(jurisdiction_dept_approvers)}')

        # 承認者候補が複数いるかチェック（いずれかのノードで複数承認者がいる場合は選択画面を表示）
        has_multiple_approvers = (len(applicant_dept_approvers) > 1) or (len(jurisdiction_dept_approvers) > 1)

        # 承認者候補が0人、または全て1人以下の場合は承認者選択をスキップしてワークフローを開始
        current_app.logger.info(f'[select_approvers] app_id={application_id}, applicant_approvers={len(applicant_dept_approvers)}, jurisdiction_approvers={len(jurisdiction_dept_approvers)}, has_multiple={has_multiple_approvers}')
        if not has_multiple_approvers:
            current_app.logger.info(f'[select_approvers] app_id={application_id}, No approvers found, starting workflow directly')
            try:
                from app.services.workflow_service import WorkflowService
                workflow_instance_id = WorkflowService.start_workflow(application_id)
                flash(f'申請を提出しました（申請ID: {application_id}）', 'success')
                return redirect(url_for('application.list'))
            except Exception as e:
                current_app.logger.error(f'ワークフロー開始エラー: {str(e)}')
                import traceback
                current_app.logger.error(traceback.format_exc())
                flash(f'ワークフローの開始に失敗しました: {str(e)}', 'danger')
                return redirect(url_for('application.list'))

        return render_template('application/select_approvers.html',
                               application_id=application_id,
                               application_title=application['application_title'],
                               application_type_name=application['application_type_name'],
                               applicant_dept_approvers=applicant_dept_approvers,
                               jurisdiction_dept_approvers=jurisdiction_dept_approvers)

    except Exception as e:
        current_app.logger.error(f'承認者選択画面エラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'承認者選択画面の表示に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.list'))


@bp.route('/confirm_approvers', methods=['POST'])
@login_required
def confirm_approvers():
    """承認者選択確認・ワークフロー開始"""
    from flask import current_app
    try:
        # application_idを取得
        application_id = request.form.get('application_id', type=int)
        if not application_id:
            flash('申請IDが取得できませんでした', 'danger')
            return redirect(url_for('application.list'))

        # 選択された承認者を取得
        applicant_dept_selected = request.form.getlist('applicant_dept_approvers')
        jurisdiction_dept_selected = request.form.getlist('jurisdiction_dept_approvers')

        # ワークフローを開始
        try:
            from app.services.workflow_service import WorkflowService
            workflow_instance_id = WorkflowService.start_workflow(
                application_id,
                selected_approvers={
                    'applicant_dept': applicant_dept_selected,
                    'jurisdiction_dept': jurisdiction_dept_selected
                }
            )
            flash(f'申請を提出しました（申請ID: {application_id}）', 'success')
            return redirect(url_for('application.list'))
        except Exception as e:
            current_app.logger.error(f'ワークフロー開始エラー: {str(e)}')
            import traceback
            current_app.logger.error(traceback.format_exc())
            flash(f'ワークフローの開始に失敗しました: {str(e)}', 'danger')
            return redirect(url_for('application.list'))

    except Exception as e:
        current_app.logger.error(f'承認者確認エラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'承認者の確認処理に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.list'))
