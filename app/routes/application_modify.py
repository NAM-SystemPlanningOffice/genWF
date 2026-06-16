"""
修正申請の提出処理
"""
from flask import Blueprint, request, redirect, url_for, flash, session
from app.utils.decorators import login_required
from app.models.application import Application
from app.models.application_field import ApplicationField
from app.models.application_type import ApplicationType
from app.utils.constants import ACTION_TYPE_MODIFY, ACTION_TYPE_DELETE
from app.services.validation_service import ValidationService

bp = Blueprint('application_modify', __name__, url_prefix='/application')


@bp.route('/modify/<int:application_type_id>/<path:resource_id>/submit', methods=['POST'])
@login_required
def submit_modify(application_type_id, resource_id):
    """修正申請の提出処理"""
    from flask import current_app
    try:
        user_id = session.get('user_id')
        applicant_shozoku = session.get('shozoku')

        if not applicant_shozoku:
            flash('所属が選択されていません。再度ログインしてください。', 'danger')
            return redirect(url_for('auth.login'))

        action = request.form.get('action')  # save_draft or submit
        current_app.logger.info(f"[submit_modify] action={action}, resource_id={resource_id}")

        # 開発中フラグのチェック（管理者以外が提出する場合）
        if action == 'submit':
            is_admin = session.get('is_admin', False)
            if not is_admin:
                app_type = ApplicationType.get_by_id(application_type_id)
                if app_type and app_type.get('is_under_development') == 'Y':
                    flash('この申請種類は現在開発中のため、提出できません。下書き保存のみ可能です。', 'danger')
                    return redirect(url_for('application.modify_with_resource',
                                            application_type_id=application_type_id,
                                            resource_id=resource_id))

        # 修正・廃止区分を取得
        modify_or_delete = request.form.get('modify_or_delete', 'modify')
        actual_action_type = ACTION_TYPE_DELETE if modify_or_delete == 'delete' else ACTION_TYPE_MODIFY

        # 実施予定日を取得
        scheduled_date_str = request.form.get('scheduled_date') or None
        scheduled_date = None

        # 実施予定日が指定されている場合は将来日付チェック
        if scheduled_date_str:
            from datetime import datetime, date
            try:
                scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
                if scheduled_date < date.today():
                    flash('実施予定日は本日以降の日付を指定してください', 'danger')
                    return redirect(url_for('application.modify_with_resource',
                                            application_type_id=application_type_id,
                                            resource_id=resource_id))
            except ValueError:
                flash('実施予定日の形式が正しくありません', 'danger')
                return redirect(url_for('application.modify_with_resource',
                                        application_type_id=application_type_id,
                                        resource_id=resource_id))

        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type:
            flash('指定された申請種類が見つかりません', 'danger')
            return redirect(url_for('application.index'))

        # 所管所属を取得（resource_jurisdiction_columnが設定されている場合）
        jurisdiction_shozoku = None
        if app_type.get('resource_jurisdiction_column'):
            jurisdiction_column = app_type['resource_jurisdiction_column']
            # リソース詳細を取得
            detail_query = app_type.get('resource_detail_query')
            if detail_query:
                from app.models.resource import Resource
                resource = Resource.get_resource_detail(detail_query, resource_id)
                if resource and jurisdiction_column in resource:
                    jurisdiction_shozoku = resource[jurisdiction_column]

        # まず下書きとして保存（バリデーションエラー時に入力値を保持するため）
        application_data = {
            'application_type_id': application_type_id,
            'action_type': actual_action_type,
            'applicant_user_id': user_id,
            'applicant_shozoku': applicant_shozoku,
            'jurisdiction_shozoku': jurisdiction_shozoku,
            'scheduled_date': scheduled_date,
            'application_title': request.form.get('application_title'),
            'resource_id': resource_id,
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

                # バリデーション実行（修正モード、resource_idを渡す）
                current_app.logger.info(f"[submit_modify] Validating field_id={field['field_id']}, value={field_value}, resource_id={resource_id}")
                is_valid, errors = ValidationService.validate_field(
                    field_id=field['field_id'],
                    value=field_value,
                    operation_type='modify',
                    resource_id=resource_id,
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
        current_app.logger.error(f'修正申請の提出に失敗: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'修正申請の提出に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.modify_with_resource',
                                application_type_id=application_type_id,
                                resource_id=resource_id))
