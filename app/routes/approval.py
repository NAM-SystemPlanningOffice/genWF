"""
承認画面のルーティング
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.utils.decorators import login_required
from app.models.approval_task import ApprovalTask

bp = Blueprint('approval', __name__, url_prefix='/approval')


@bp.route('/tasks')
@login_required
def task_list():
    """承認待ちタスク一覧"""
    from flask import current_app
    try:
        user_id = session.get('user_id')
        current_app.logger.info(f'[task_list] START: user={user_id}')
        if not user_id:
            flash('ログインが必要です', 'danger')
            return redirect(url_for('auth.login'))

        # データベースから承認待ちタスクを取得
        tasks = ApprovalTask.get_pending_tasks(user_id)
        current_app.logger.info(f'[task_list] END: tasks count={len(tasks)}')

        return render_template('approval/task_list.html', tasks=tasks)
    except Exception as e:
        flash(f'承認タスクの取得に失敗しました: {str(e)}', 'danger')
        return render_template('approval/task_list.html', tasks=[])


@bp.route('/task/<int:node_instance_id>')
@login_required
def approve_task(node_instance_id):
    """承認タスク詳細・承認画面"""
    from flask import current_app

    try:
        user_id = session.get('user_id')
        if not user_id:
            flash('ログインが必要です', 'danger')
            return redirect(url_for('auth.login'))

        # application_idが指定されている場合は、そこから承認タスクを探す
        application_id = request.args.get('application_id', type=int)
        if application_id and node_instance_id == 0:
            # application_idから承認待ちのnode_instance_idを取得
            from app.utils.db import get_db_connection, dict_fetchone
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """
                SELECT na.node_instance_id
                FROM T_WORKFLOW_NODE_APPROVER na
                INNER JOIN T_WORKFLOW_NODE_INSTANCE ni ON na.node_instance_id = ni.node_instance_id
                INNER JOIN T_WORKFLOW_INSTANCE wi ON ni.workflow_instance_id = wi.workflow_instance_id
                WHERE wi.application_id = :application_id
                  AND na.approver_user_id = :user_id
                  AND ni.node_status = 'pending'
                  AND wi.workflow_status = 'in_progress'
                ORDER BY ni.node_seq
                FETCH FIRST 1 ROWS ONLY
            """
            cursor.execute(sql, {'application_id': application_id, 'user_id': user_id})
            result = dict_fetchone(cursor)
            cursor.close()

            if result:
                node_instance_id = result['node_instance_id']
            else:
                flash('承認待ちのタスクが見つかりません', 'danger')
                return redirect(url_for('application.list'))

        # タスク詳細を取得（承認権限チェック付き）
        task = ApprovalTask.get_task_detail(node_instance_id, user_id)
        if not task:
            flash('承認タスクが見つかりません、または承認権限がありません', 'danger')
            return redirect(url_for('approval.task_list'))

        # 申請詳細を取得
        from app.models.application import Application
        from app.models.application_detail import ApplicationDetail
        from app.models.workflow import WorkflowNodeInstance
        from app.models.application_type import ApplicationType

        application = Application.get_by_id(task['application_id'])
        details = ApplicationDetail.get_by_application(task['application_id'])

        # 申請種類を取得して複数レコード形式かチェック
        app_type = ApplicationType.get_by_id(application['application_type_id'])
        is_multi_record = app_type and app_type.get('is_multi_record') == 'Y'

        # 複数レコード形式の場合はdetail_seqでグループ化
        if is_multi_record:
            details_grouped = ApplicationDetail.get_grouped_by_seq(task['application_id'])
        else:
            details_grouped = None

        # ワークフロー全体の進捗を取得
        workflow_nodes = WorkflowNodeInstance.get_by_workflow(task['workflow_instance_id'])

        # 承認者候補一覧を取得
        all_approvers = ApprovalTask.get_approvers_for_node(node_instance_id)

        # 現在のユーザーのapprover_groupを取得
        current_user_approver = next((a for a in all_approvers if a['approver_user_id'] == user_id), None)
        current_user_group = current_user_approver.get('approver_group') if current_user_approver else None

        # approver_groupがある場合は、同じグループの承認者のみを表示
        if current_user_group:
            approvers = [a for a in all_approvers if a.get('approver_group') == current_user_group]
            current_app.logger.info(f'[approve_task] user={user_id}, group={current_user_group}, filtered approvers={len(approvers)}/{len(all_approvers)}')
        else:
            approvers = all_approvers
            current_app.logger.info(f'[approve_task] user={user_id}, no group filter, approvers={len(approvers)}')

        return render_template('approval/approve_task.html',
                               task=task,
                               application=application,
                               details=details,
                               details_grouped=details_grouped,
                               is_multi_record=is_multi_record,
                               workflow_nodes=workflow_nodes,
                               approvers=approvers)

    except Exception as e:
        current_app.logger.error(f'承認タスク詳細取得エラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'承認タスクの取得に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('approval.task_list'))


@bp.route('/task/<int:node_instance_id>/action', methods=['POST'])
@login_required
def action_task(node_instance_id):
    """承認タスクに対するアクション（承認/却下/差し戻し）"""
    from flask import current_app
    from app.utils.user_log import log_user_action

    try:
        user_id = session.get('user_id')
        if not user_id:
            flash('ログインが必要です', 'danger')
            return redirect(url_for('auth.login'))

        action = request.form.get('action')  # approve or reject
        comment = request.form.get('comment', '')

        # 承認権限チェック
        task = ApprovalTask.get_task_detail(node_instance_id, user_id)
        if not task:
            flash('承認権限がありません', 'danger')
            return redirect(url_for('approval.task_list'))

        # 承認/却下/差し戻し処理
        from app.services.workflow_service import WorkflowService
        from app.models.application import Application
        from app.models.application_type import ApplicationType

        # ログ記録用の情報を取得
        node_name = task.get('node_name')
        application = Application.get_by_id(task['application_id'])
        app_type = ApplicationType.get_by_id(application['application_type_id']) if application else None
        application_type_code = app_type.get('application_type_code') if app_type else None

        if action == 'approve':
            WorkflowService.approve_node(node_instance_id, user_id, comment)
            log_user_action(user_id, 'approve', task['application_id'], application_type_code, node_name)
            flash('承認しました', 'success')
        elif action == 'return':
            WorkflowService.return_node(node_instance_id, user_id, comment)
            log_user_action(user_id, 'return', task['application_id'], application_type_code, node_name)
            flash('差し戻しました。申請者が修正して再提出できます。', 'info')
        elif action == 'reject':
            WorkflowService.reject_node(node_instance_id, user_id, comment)
            log_user_action(user_id, 'reject', task['application_id'], application_type_code, node_name)
            flash('却下しました', 'info')
        else:
            flash('不正なアクションです', 'danger')
            return redirect(url_for('approval.task_list'))

        return redirect(url_for('approval.task_list'))

    except Exception as e:
        current_app.logger.error(f'承認アクションエラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'承認処理に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('approval.task_list'))
