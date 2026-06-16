"""
管理画面のルーティング
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.utils.decorators import login_required, admin_required

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
@admin_required
def index():
    """管理画面トップ"""
    return render_template('admin/index.html')


# ==========================================
# 申請タイプ管理
# ==========================================

@bp.route('/application-types')
@admin_required
def application_type_list():
    """申請タイプ一覧"""
    from app.models.admin.application_type import ApplicationType

    try:
        application_types = ApplicationType.get_all()
        return render_template('admin/application_type_list.html',
                             application_types=application_types)
    except Exception as e:
        flash(f'申請タイプの取得に失敗しました: {str(e)}', 'error')
        return render_template('admin/application_type_list.html',
                             application_types=[])


@bp.route('/application-types/new')
@admin_required
def application_type_new():
    """申請タイプ新規作成"""
    from app.models.admin.workflow_definition import WorkflowDefinition

    try:
        # ワークフロー一覧を取得
        workflows = WorkflowDefinition.get_all()
        return render_template('admin/application_type_edit.html',
                             application_type=None,
                             workflows=workflows,
                             mode='new')
    except Exception as e:
        flash(f'画面の表示に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.application_type_list'))


@bp.route('/application-types/<int:application_type_id>/edit')
@admin_required
def application_type_edit(application_type_id):
    """申請タイプ編集"""
    from app.models.admin.application_type import ApplicationType
    from app.models.admin.workflow_definition import WorkflowDefinition

    try:
        application_type = ApplicationType.get_by_id(application_type_id)
        if not application_type:
            flash('申請タイプが見つかりません', 'error')
            return redirect(url_for('admin.application_type_list'))

        workflows = WorkflowDefinition.get_all()
        return render_template('admin/application_type_edit.html',
                             application_type=application_type,
                             workflows=workflows,
                             mode='edit')
    except Exception as e:
        flash(f'申請タイプの取得に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.application_type_list'))


@bp.route('/application-types/save', methods=['POST'])
@admin_required
def application_type_save():
    """申請タイプ保存"""
    from app.models.admin.application_type import ApplicationType
    from app.models.admin.audit_log import AuditLog

    try:
        application_type_id = request.form.get('application_type_id')

        # バリデーション
        validation_errors = []

        if not request.form.get('application_type_code'):
            validation_errors.append('申請タイプコードは必須です')

        if not request.form.get('application_type_name'):
            validation_errors.append('申請タイプ名は必須です')

        if not request.form.get('workflow_definition_id'):
            validation_errors.append('ワークフロー定義IDは必須です')

        # バリデーションエラーがある場合は入力画面に戻る
        if validation_errors:
            for error in validation_errors:
                flash(error, 'danger')

            # 入力値を保持して編集画面に戻る
            application_type_data = {
                'application_type_id': application_type_id,
                'application_type_code': request.form.get('application_type_code'),
                'application_type_name': request.form.get('application_type_name'),
                'description': request.form.get('description'),
                'is_multi_record': request.form.get('is_multi_record'),
                'record_add_mode': request.form.get('record_add_mode', 'select'),
                'support_create': request.form.get('support_create'),
                'support_modify': request.form.get('support_modify'),
                'support_delete': request.form.get('support_delete'),
                'jurisdiction_restriction': request.form.get('jurisdiction_restriction', 'any'),
                'allowed_shozoku_list': request.form.get('allowed_shozoku_list'),
                'allowed_user_list': request.form.get('allowed_user_list'),
                'workflow_definition_id': request.form.get('workflow_definition_id'),
                'resource_search_query': request.form.get('resource_search_query'),
                'resource_detail_query': request.form.get('resource_detail_query'),
                'resource_member_query': request.form.get('resource_member_query'),
                'resource_validation_query': request.form.get('resource_validation_query'),
                'resource_jurisdiction_column': request.form.get('resource_jurisdiction_column'),
                'is_under_development': request.form.get('is_under_development'),
                'is_active': request.form.get('is_active', 'Y')
            }

            # ワークフロー定義一覧を取得
            from app.models.admin.workflow_definition import WorkflowDefinition
            workflows = WorkflowDefinition.get_all()

            mode = 'edit' if application_type_id else 'new'
            return render_template('admin/application_type_edit.html',
                                 application_type=application_type_data,
                                 workflows=workflows,
                                 mode=mode)

        data = {
            'application_type_code': request.form.get('application_type_code'),
            'application_type_name': request.form.get('application_type_name'),
            'description': request.form.get('description'),
            'is_multi_record': 'Y' if request.form.get('is_multi_record') else 'N',
            'record_add_mode': request.form.get('record_add_mode', 'select'),
            'support_create': 'Y' if request.form.get('support_create') else 'N',
            'support_modify': 'Y' if request.form.get('support_modify') else 'N',
            'support_delete': 'Y' if request.form.get('support_delete') else 'N',
            'jurisdiction_restriction': request.form.get('jurisdiction_restriction', 'any'),
            'allowed_shozoku_list': request.form.get('allowed_shozoku_list'),
            'allowed_user_list': request.form.get('allowed_user_list'),
            'workflow_definition_id': request.form.get('workflow_definition_id'),
            'resource_search_query': request.form.get('resource_search_query'),
            'resource_detail_query': request.form.get('resource_detail_query'),
            'resource_member_query': request.form.get('resource_member_query'),
            'resource_validation_query': request.form.get('resource_validation_query'),
            'resource_jurisdiction_column': request.form.get('resource_jurisdiction_column'),
            'is_under_development': 'Y' if request.form.get('is_under_development') else 'N',
            'is_active': 'Y' if request.form.get('is_active') else 'N'
        }

        if application_type_id:
            # 更新
            ApplicationType.update(int(application_type_id), data)
            flash('申請タイプを更新しました', 'success')

            # 監査ログを記録
            AuditLog.log(
                user_id=session.get('user_id'),
                user_name=session.get('user_name'),
                operation_type='UPDATE',
                table_name='M_APPLICATION_TYPE',
                record_id=application_type_id,
                operation_detail={
                    'application_type_name': data['application_type_name'],
                    'application_type_code': data['application_type_code']
                }
            )
        else:
            # 新規作成
            new_id = ApplicationType.create(data)
            flash('申請タイプを作成しました', 'success')
            application_type_id = new_id

            # 監査ログを記録
            AuditLog.log(
                user_id=session.get('user_id'),
                user_name=session.get('user_name'),
                operation_type='CREATE',
                table_name='M_APPLICATION_TYPE',
                record_id=application_type_id,
                operation_detail={
                    'application_type_name': data['application_type_name'],
                    'application_type_code': data['application_type_code']
                }
            )

        # 次のステップへ
        next_step = request.form.get('next_step', 'list')
        if next_step == 'fields':
            return redirect(url_for('admin.application_type_fields',
                                  application_type_id=application_type_id))
        else:
            return redirect(url_for('admin.application_type_list'))

    except Exception as e:
        flash(f'申請タイプの保存に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.application_type_list'))


@bp.route('/application-types/<int:application_type_id>/fields')
@admin_required
def application_type_fields(application_type_id):
    """申請タイプのフィールド管理"""
    from app.models.admin.application_type import ApplicationType
    from app.models.admin.application_field import ApplicationField

    try:
        application_type = ApplicationType.get_by_id(application_type_id)
        if not application_type:
            flash('申請タイプが見つかりません', 'error')
            return redirect(url_for('admin.application_type_list'))

        fields = ApplicationField.get_by_application_type(application_type_id)

        return render_template('admin/application_type_fields.html',
                             application_type=application_type,
                             fields=fields)
    except Exception as e:
        flash(f'フィールドの取得に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.application_type_list'))


@bp.route('/application-types/<int:application_type_id>/fields/new')
@admin_required
def field_new(application_type_id):
    """フィールド新規作成"""
    from app.models.admin.application_type import ApplicationType
    from app.models.admin.validation_rule import ValidationRule
    from app.models.admin.pulldown_group import PulldownGroup

    try:
        application_type = ApplicationType.get_by_id(application_type_id)
        if not application_type:
            flash('申請タイプが見つかりません', 'error')
            return redirect(url_for('admin.application_type_list'))

        validation_rules = ValidationRule.get_all()
        pulldown_groups = PulldownGroup.get_all()

        return render_template('admin/field_edit.html',
                             application_type=application_type,
                             field=None,
                             validation_rules=validation_rules,
                             pulldown_groups=pulldown_groups,
                             mode='new')
    except Exception as e:
        flash(f'画面の表示に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.application_type_fields',
                              application_type_id=application_type_id))


@bp.route('/fields/<int:field_id>/edit')
@admin_required
def field_edit(field_id):
    """フィールド編集"""
    from app.models.admin.application_field import ApplicationField
    from app.models.admin.application_type import ApplicationType
    from app.models.admin.validation_rule import ValidationRule
    from app.models.admin.pulldown_group import PulldownGroup
    from app.models.admin.field_validation import FieldValidation

    try:
        field = ApplicationField.get_by_id(field_id)
        if not field:
            flash('フィールドが見つかりません', 'error')
            return redirect(url_for('admin.application_type_list'))

        application_type = ApplicationType.get_by_id(field['application_type_id'])
        validation_rules = ValidationRule.get_all()
        pulldown_groups = PulldownGroup.get_all()
        assigned_validations = FieldValidation.get_by_field(field_id)

        return render_template('admin/field_edit.html',
                             application_type=application_type,
                             field=field,
                             validation_rules=validation_rules,
                             pulldown_groups=pulldown_groups,
                             assigned_validations=assigned_validations,
                             mode='edit')
    except Exception as e:
        flash(f'フィールドの取得に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.application_type_list'))


@bp.route('/fields/save', methods=['POST'])
@admin_required
def field_save():
    """フィールド保存"""
    from app.models.admin.application_field import ApplicationField
    from app.models.admin.field_validation import FieldValidation
    from app.models.admin.audit_log import AuditLog

    try:
        field_id = request.form.get('field_id')
        application_type_id = request.form.get('application_type_id')

        data = {
            'application_type_id': application_type_id,
            'field_code': request.form.get('field_code'),
            'field_name': request.form.get('field_name'),
            'field_type': request.form.get('field_type', 'text'),
            'is_required_create': 'Y' if request.form.get('is_required_create') else 'N',
            'is_required_modify': 'Y' if request.form.get('is_required_modify') else 'N',
            'is_required_delete': 'Y' if request.form.get('is_required_delete') else 'N',
            'is_editable_modify': 'Y' if request.form.get('is_editable_modify') else 'N',
            'is_visible': 'Y' if request.form.get('is_visible') else 'N',
            'is_key_field': 'Y' if request.form.get('is_key_field') else 'N',
            'pulldown_group_id': request.form.get('pulldown_group_id') or None,
            'resource_column_name': request.form.get('resource_column_name'),
            'resource_label_column': request.form.get('resource_label_column'),
            'display_order': request.form.get('display_order') or None,
            'default_value': request.form.get('default_value'),
            'placeholder': request.form.get('placeholder'),
            'help_text': request.form.get('help_text')
        }

        if field_id:
            # 更新
            ApplicationField.update(int(field_id), data)
            flash('フィールドを更新しました', 'success')

            # 監査ログを記録
            AuditLog.log(
                user_id=session.get('user_id'),
                user_name=session.get('user_name'),
                operation_type='UPDATE',
                table_name='M_APPLICATION_FIELD',
                record_id=field_id,
                operation_detail={
                    'field_name': data['field_name'],
                    'field_code': data['field_code'],
                    'application_type_id': application_type_id
                }
            )
        else:
            # 新規作成
            field_id = ApplicationField.create(data)
            flash('フィールドを作成しました', 'success')

            # 監査ログを記録
            AuditLog.log(
                user_id=session.get('user_id'),
                user_name=session.get('user_name'),
                operation_type='CREATE',
                table_name='M_APPLICATION_FIELD',
                record_id=field_id,
                operation_detail={
                    'field_name': data['field_name'],
                    'field_code': data['field_code'],
                    'application_type_id': application_type_id
                }
            )

        # バリデーションルールの割り当て
        # 既存の割り当てを全削除
        if field_id:
            # 既存のバリデーションルールIDを取得
            existing = FieldValidation.get_by_field(int(field_id))
            for ev in existing:
                FieldValidation.remove(ev['field_validation_id'])

            # 新しい割り当てを追加
            validation_rule_ids = request.form.getlist('validation_rule_ids')
            for order, rule_id in enumerate(validation_rule_ids, start=1):
                if rule_id:
                    FieldValidation.add(int(field_id), int(rule_id), order)

        return redirect(url_for('admin.application_type_fields',
                              application_type_id=application_type_id))

    except Exception as e:
        flash(f'フィールドの保存に失敗しました: {str(e)}', 'error')
        application_type_id = request.form.get('application_type_id')
        if application_type_id:
            return redirect(url_for('admin.application_type_fields',
                                  application_type_id=application_type_id))
        return redirect(url_for('admin.application_type_list'))


@bp.route('/fields/<int:field_id>/delete', methods=['POST'])
@admin_required
def field_delete(field_id):
    """フィールド削除（論理削除）"""
    from app.models.admin.application_field import ApplicationField
    from app.models.admin.audit_log import AuditLog

    try:
        field = ApplicationField.get_by_id(field_id)
        if not field:
            flash('フィールドが見つかりません', 'error')
            return redirect(url_for('admin.application_type_list'))

        application_type_id = field['application_type_id']

        ApplicationField.delete(field_id)

        # 監査ログを記録
        AuditLog.log(
            user_id=session.get('user_id'),
            user_name=session.get('user_name'),
            operation_type='DELETE',
            table_name='M_APPLICATION_FIELD',
            record_id=field_id,
            operation_detail={
                'field_name': field['field_name'],
                'field_code': field['field_code'],
                'application_type_id': application_type_id,
                'action': '論理削除'
            }
        )

        flash('フィールドを削除しました', 'success')

        return redirect(url_for('admin.application_type_fields',
                              application_type_id=application_type_id))

    except Exception as e:
        flash(f'フィールドの削除に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.application_type_list'))


# ==========================================
# バリデーションルール管理
# ==========================================

@bp.route('/validation-rules')
@admin_required
def validation_rule_list():
    """バリデーションルール一覧"""
    from app.models.admin.validation_rule import ValidationRule

    try:
        rules = ValidationRule.get_all()
        return render_template('admin/validation_rule_list.html', rules=rules)
    except Exception as e:
        flash(f'バリデーションルールの取得に失敗しました: {str(e)}', 'error')
        return render_template('admin/validation_rule_list.html', rules=[])


@bp.route('/validation-rules/new')
@admin_required
def validation_rule_new():
    """バリデーションルール新規作成"""
    return render_template('admin/validation_rule_edit.html',
                         rule=None,
                         mode='new')


@bp.route('/validation-rules/<int:validation_rule_id>/edit')
@admin_required
def validation_rule_edit(validation_rule_id):
    """バリデーションルール編集"""
    from app.models.admin.validation_rule import ValidationRule

    try:
        rule = ValidationRule.get_by_id(validation_rule_id)
        if not rule:
            flash('バリデーションルールが見つかりません', 'error')
            return redirect(url_for('admin.validation_rule_list'))

        return render_template('admin/validation_rule_edit.html',
                             rule=rule,
                             mode='edit')
    except Exception as e:
        flash(f'バリデーションルールの取得に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.validation_rule_list'))


@bp.route('/validation-rules/save', methods=['POST'])
@admin_required
def validation_rule_save():
    """バリデーションルール保存"""
    from app.models.admin.validation_rule import ValidationRule

    try:
        validation_rule_id = request.form.get('validation_rule_id')
        data = {
            'rule_code': request.form.get('rule_code'),
            'rule_name': request.form.get('rule_name'),
            'rule_type': request.form.get('rule_type'),
            'rule_parameter': request.form.get('rule_parameter'),
            'error_message': request.form.get('error_message'),
            'description': request.form.get('description'),
            'is_active': 'Y' if request.form.get('is_active') else 'N'
        }

        if validation_rule_id:
            # 更新
            ValidationRule.update(int(validation_rule_id), data)
            flash('バリデーションルールを更新しました', 'success')
        else:
            # 新規作成
            ValidationRule.create(data)
            flash('バリデーションルールを作成しました', 'success')

        return redirect(url_for('admin.validation_rule_list'))

    except Exception as e:
        flash(f'バリデーションルールの保存に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.validation_rule_list'))


@bp.route('/validation-rules/<int:validation_rule_id>/delete', methods=['POST'])
@admin_required
def validation_rule_delete(validation_rule_id):
    """バリデーションルール削除"""
    from app.models.admin.validation_rule import ValidationRule
    from app.models.admin.audit_log import AuditLog

    try:
        rule = ValidationRule.get_by_id(validation_rule_id)
        ValidationRule.delete(validation_rule_id)

        # 監査ログを記録
        if rule:
            AuditLog.log(
                user_id=session.get('user_id'),
                user_name=session.get('user_name'),
                operation_type='DELETE',
                table_name='M_VALIDATION_RULE',
                record_id=validation_rule_id,
                operation_detail={
                    'rule_name': rule.get('rule_name'),
                    'rule_code': rule.get('rule_code')
                }
            )

        flash('バリデーションルールを削除しました', 'success')
        return redirect(url_for('admin.validation_rule_list'))

    except Exception as e:
        flash(f'バリデーションルールの削除に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.validation_rule_list'))


# ==========================================
# プルダウングループ管理
# ==========================================

@bp.route('/pulldown-groups')
@admin_required
def pulldown_group_list():
    """プルダウングループ一覧"""
    from app.models.admin.pulldown_group import PulldownGroup

    try:
        groups = PulldownGroup.get_all()
        return render_template('admin/pulldown_group_list.html', groups=groups)
    except Exception as e:
        flash(f'プルダウングループの取得に失敗しました: {str(e)}', 'error')
        return render_template('admin/pulldown_group_list.html', groups=[])


@bp.route('/pulldown-groups/new')
@admin_required
def pulldown_group_new():
    """プルダウングループ新規作成"""
    return render_template('admin/pulldown_group_edit.html',
                         group=None,
                         mode='new')


@bp.route('/pulldown-groups/<int:pulldown_group_id>/edit')
@admin_required
def pulldown_group_edit(pulldown_group_id):
    """プルダウングループ編集"""
    from app.models.admin.pulldown_group import PulldownGroup

    try:
        group = PulldownGroup.get_by_id(pulldown_group_id)
        if not group:
            flash('プルダウングループが見つかりません', 'error')
            return redirect(url_for('admin.pulldown_group_list'))

        return render_template('admin/pulldown_group_edit.html',
                             group=group,
                             mode='edit')
    except Exception as e:
        flash(f'プルダウングループの取得に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.pulldown_group_list'))


@bp.route('/pulldown-groups/save', methods=['POST'])
@admin_required
def pulldown_group_save():
    """プルダウングループ保存"""
    from app.models.admin.pulldown_group import PulldownGroup

    try:
        pulldown_group_id = request.form.get('pulldown_group_id')
        data = {
            'group_code': request.form.get('group_code'),
            'group_name': request.form.get('group_name'),
            'description': request.form.get('description'),
            'is_dynamic': 'Y' if request.form.get('is_dynamic') else 'N',
            'dynamic_query': request.form.get('dynamic_query')
        }

        if pulldown_group_id:
            # 更新
            PulldownGroup.update(int(pulldown_group_id), data)
            flash('プルダウングループを更新しました', 'success')
        else:
            # 新規作成
            pulldown_group_id = PulldownGroup.create(data)
            flash('プルダウングループを作成しました', 'success')

        # 次のステップへ
        next_step = request.form.get('next_step', 'list')
        if next_step == 'options':
            return redirect(url_for('admin.pulldown_group_options',
                                  pulldown_group_id=pulldown_group_id))
        else:
            return redirect(url_for('admin.pulldown_group_list'))

    except Exception as e:
        flash(f'プルダウングループの保存に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.pulldown_group_list'))


@bp.route('/pulldown-groups/<int:pulldown_group_id>/delete', methods=['POST'])
@admin_required
def pulldown_group_delete(pulldown_group_id):
    """プルダウングループ削除"""
    from app.models.admin.pulldown_group import PulldownGroup
    from app.models.admin.audit_log import AuditLog

    try:
        group = PulldownGroup.get_by_id(pulldown_group_id)
        PulldownGroup.delete(pulldown_group_id)

        # 監査ログを記録
        if group:
            AuditLog.log(
                user_id=session.get('user_id'),
                user_name=session.get('user_name'),
                operation_type='DELETE',
                table_name='M_PULLDOWN_GROUP',
                record_id=pulldown_group_id,
                operation_detail={
                    'group_name': group.get('group_name'),
                    'group_code': group.get('group_code')
                }
            )

        flash('プルダウングループを削除しました', 'success')
        return redirect(url_for('admin.pulldown_group_list'))

    except Exception as e:
        flash(f'プルダウングループの削除に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.pulldown_group_list'))


@bp.route('/pulldown-groups/<int:pulldown_group_id>/options')
@admin_required
def pulldown_group_options(pulldown_group_id):
    """プルダウン選択肢管理"""
    from app.models.admin.pulldown_group import PulldownGroup
    from app.models.admin.pulldown_option import PulldownOption

    try:
        group = PulldownGroup.get_by_id(pulldown_group_id)
        if not group:
            flash('プルダウングループが見つかりません', 'error')
            return redirect(url_for('admin.pulldown_group_list'))

        options = PulldownOption.get_by_group(pulldown_group_id)

        return render_template('admin/pulldown_group_options.html',
                             group=group,
                             options=options)
    except Exception as e:
        flash(f'選択肢の取得に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.pulldown_group_list'))


@bp.route('/pulldown-options/save', methods=['POST'])
@admin_required
def pulldown_option_save():
    """プルダウン選択肢保存"""
    from app.models.admin.pulldown_option import PulldownOption

    try:
        option_id = request.form.get('option_id')
        pulldown_group_id = request.form.get('pulldown_group_id')

        data = {
            'pulldown_group_id': pulldown_group_id,
            'option_value': request.form.get('option_value'),
            'option_label': request.form.get('option_label'),
            'display_order': request.form.get('display_order') or None,
            'is_active': 'Y' if request.form.get('is_active') else 'N',
            'parent_option_id': request.form.get('parent_option_id') or None
        }

        if option_id:
            # 更新
            PulldownOption.update(int(option_id), data)
            flash('選択肢を更新しました', 'success')
        else:
            # 新規作成
            PulldownOption.create(data)
            flash('選択肢を作成しました', 'success')

        return redirect(url_for('admin.pulldown_group_options',
                              pulldown_group_id=pulldown_group_id))

    except Exception as e:
        flash(f'選択肢の保存に失敗しました: {str(e)}', 'error')
        pulldown_group_id = request.form.get('pulldown_group_id')
        if pulldown_group_id:
            return redirect(url_for('admin.pulldown_group_options',
                                  pulldown_group_id=pulldown_group_id))
        return redirect(url_for('admin.pulldown_group_list'))


@bp.route('/pulldown-options/<int:option_id>/delete', methods=['POST'])
@admin_required
def pulldown_option_delete(option_id):
    """プルダウン選択肢削除"""
    from app.models.admin.pulldown_option import PulldownOption
    from app.models.admin.audit_log import AuditLog

    try:
        option = PulldownOption.get_by_id(option_id)
        if not option:
            flash('選択肢が見つかりません', 'error')
            return redirect(url_for('admin.pulldown_group_list'))

        pulldown_group_id = option['pulldown_group_id']

        PulldownOption.delete(option_id)

        # 監査ログを記録
        AuditLog.log(
            user_id=session.get('user_id'),
            user_name=session.get('user_name'),
            operation_type='DELETE',
            table_name='M_PULLDOWN_OPTION',
            record_id=option_id,
            operation_detail={
                'option_label': option.get('option_label'),
                'option_value': option.get('option_value'),
                'pulldown_group_id': pulldown_group_id
            }
        )

        flash('選択肢を削除しました', 'success')

        return redirect(url_for('admin.pulldown_group_options',
                              pulldown_group_id=pulldown_group_id))

    except Exception as e:
        flash(f'選択肢の削除に失敗しました: {str(e)}', 'error')
        return redirect(url_for('admin.pulldown_group_list'))


# ==========================================
# ワークフロー定義管理
# ==========================================

@bp.route('/workflows')
@admin_required
def workflow_list():
    """ワークフロー定義一覧"""
    from app.models.admin.workflow_definition import WorkflowDefinition

    try:
        workflows = WorkflowDefinition.get_all(include_inactive=True)
        return render_template('admin/workflow_list.html', workflows=workflows)
    except Exception as e:
        flash(f'ワークフロー定義の取得に失敗しました: {str(e)}', 'danger')
        import traceback
        traceback.print_exc()
        return redirect(url_for('admin.index'))


@bp.route('/workflows/new')
@admin_required
def workflow_new():
    """ワークフロー定義作成画面"""
    return render_template('admin/workflow_edit.html', mode='new', workflow=None)


@bp.route('/workflows/<int:workflow_definition_id>')
@admin_required
def workflow_detail(workflow_definition_id):
    """ワークフロー定義詳細（ノード一覧）"""
    from app.models.admin.workflow_definition import WorkflowDefinition

    try:
        workflow = WorkflowDefinition.get_by_id(workflow_definition_id)
        if not workflow:
            flash('ワークフロー定義が見つかりません', 'danger')
            return redirect(url_for('admin.workflow_list'))

        nodes = WorkflowDefinition.get_nodes(workflow_definition_id)

        return render_template('admin/workflow_detail.html',
                             workflow=workflow,
                             nodes=nodes)
    except Exception as e:
        flash(f'ワークフロー定義の取得に失敗しました: {str(e)}', 'danger')
        import traceback
        traceback.print_exc()
        return redirect(url_for('admin.workflow_list'))


@bp.route('/workflows/<int:workflow_definition_id>/edit')
@admin_required
def workflow_edit(workflow_definition_id):
    """ワークフロー定義編集画面"""
    from app.models.admin.workflow_definition import WorkflowDefinition

    try:
        workflow = WorkflowDefinition.get_by_id(workflow_definition_id)
        if not workflow:
            flash('ワークフロー定義が見つかりません', 'danger')
            return redirect(url_for('admin.workflow_list'))

        return render_template('admin/workflow_edit.html',
                             mode='edit',
                             workflow=workflow)
    except Exception as e:
        flash(f'ワークフロー定義の取得に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('admin.workflow_list'))


@bp.route('/workflows/save', methods=['POST'])
@admin_required
def workflow_save():
    """ワークフロー定義保存"""
    from app.models.admin.workflow_definition import WorkflowDefinition

    try:
        workflow_definition_id = request.form.get('workflow_definition_id')

        data = {
            'workflow_name': request.form.get('workflow_name'),
            'workflow_code': request.form.get('workflow_code'),
            'description': request.form.get('description'),
            'is_active': 'Y' if request.form.get('is_active') else 'N',
            'version': request.form.get('version', 1)
        }

        if workflow_definition_id:
            # 更新
            WorkflowDefinition.update(int(workflow_definition_id), data)
            flash('ワークフロー定義を更新しました', 'success')
            workflow_definition_id = int(workflow_definition_id)
        else:
            # 新規作成
            workflow_definition_id = WorkflowDefinition.create(data)
            flash('ワークフロー定義を作成しました', 'success')

        # 次の画面へ
        next_step = request.form.get('next_step', 'list')
        if next_step == 'nodes':
            return redirect(url_for('admin.workflow_detail',
                                  workflow_definition_id=workflow_definition_id))
        else:
            return redirect(url_for('admin.workflow_list'))

    except Exception as e:
        flash(f'ワークフロー定義の保存に失敗しました: {str(e)}', 'danger')
        import traceback
        traceback.print_exc()
        return redirect(url_for('admin.workflow_list'))


@bp.route('/workflows/<int:workflow_definition_id>/delete', methods=['POST'])
@admin_required
def workflow_delete(workflow_definition_id):
    """ワークフロー定義削除"""
    from app.models.admin.workflow_definition import WorkflowDefinition

    try:
        WorkflowDefinition.delete(workflow_definition_id)
        flash('ワークフロー定義を削除しました', 'success')
    except Exception as e:
        flash(f'ワークフロー定義の削除に失敗しました: {str(e)}', 'danger')

    return redirect(url_for('admin.workflow_list'))


# ==========================================
# ワークフローノード定義管理
# ==========================================

@bp.route('/workflows/<int:workflow_definition_id>/nodes/new')
@admin_required
def workflow_node_new(workflow_definition_id):
    """ワークフローノード定義作成画面"""
    from app.models.admin.workflow_definition import WorkflowDefinition

    try:
        workflow = WorkflowDefinition.get_by_id(workflow_definition_id)
        if not workflow:
            flash('ワークフロー定義が見つかりません', 'danger')
            return redirect(url_for('admin.workflow_list'))

        # 次のnode_seqを計算
        nodes = WorkflowDefinition.get_nodes(workflow_definition_id)
        next_seq = max([n['node_seq'] for n in nodes], default=0) + 10

        return render_template('admin/workflow_node_edit.html',
                             mode='new',
                             workflow=workflow,
                             node=None,
                             next_seq=next_seq)
    except Exception as e:
        flash(f'画面表示に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('admin.workflow_list'))


@bp.route('/workflows/<int:workflow_definition_id>/nodes/<int:node_definition_id>/edit')
@admin_required
def workflow_node_edit(workflow_definition_id, node_definition_id):
    """ワークフローノード定義編集画面"""
    from app.models.admin.workflow_definition import WorkflowDefinition
    from app.models.admin.workflow_node_definition import WorkflowNodeDefinition

    try:
        workflow = WorkflowDefinition.get_by_id(workflow_definition_id)
        node = WorkflowNodeDefinition.get_by_id(node_definition_id)

        if not workflow or not node:
            flash('ワークフロー定義またはノード定義が見つかりません', 'danger')
            return redirect(url_for('admin.workflow_list'))

        return render_template('admin/workflow_node_edit.html',
                             mode='edit',
                             workflow=workflow,
                             node=node,
                             next_seq=None)
    except Exception as e:
        flash(f'画面表示に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('admin.workflow_list'))


@bp.route('/workflows/<int:workflow_definition_id>/nodes/save', methods=['POST'])
@admin_required
def workflow_node_save(workflow_definition_id):
    """ワークフローノード定義保存"""
    from app.models.admin.workflow_node_definition import WorkflowNodeDefinition

    try:
        node_definition_id = request.form.get('node_definition_id')

        data = {
            'workflow_definition_id': workflow_definition_id,
            'node_seq': request.form.get('node_seq'),
            'node_name': request.form.get('node_name'),
            'node_type': request.form.get('node_type'),
            'action_type': request.form.get('action_type', 'approval'),
            'specific_value': request.form.get('specific_value'),
            'skip_condition': request.form.get('skip_condition'),
            'is_report_only': 'Y' if request.form.get('is_report_only') else 'N',
            'approver_selection_required': 'Y' if request.form.get('approver_selection_required') else 'N'
        }

        if node_definition_id:
            # 更新
            WorkflowNodeDefinition.update(int(node_definition_id), data)
            flash('ノード定義を更新しました', 'success')
        else:
            # 新規作成
            WorkflowNodeDefinition.create(data)
            flash('ノード定義を作成しました', 'success')

        return redirect(url_for('admin.workflow_detail',
                              workflow_definition_id=workflow_definition_id))

    except Exception as e:
        flash(f'ノード定義の保存に失敗しました: {str(e)}', 'danger')
        import traceback
        traceback.print_exc()
        return redirect(url_for('admin.workflow_detail',
                              workflow_definition_id=workflow_definition_id))


@bp.route('/workflows/<int:workflow_definition_id>/nodes/<int:node_definition_id>/delete', methods=['POST'])
@admin_required
def workflow_node_delete(workflow_definition_id, node_definition_id):
    """ワークフローノード定義削除"""
    from app.models.admin.workflow_node_definition import WorkflowNodeDefinition

    try:
        WorkflowNodeDefinition.delete(node_definition_id)
        flash('ノード定義を削除しました', 'success')
    except Exception as e:
        flash(f'ノード定義の削除に失敗しました: {str(e)}', 'danger')

    return redirect(url_for('admin.workflow_detail',
                          workflow_definition_id=workflow_definition_id))
