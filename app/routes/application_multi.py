"""
複数レコード入力申請のルーティング
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.utils.decorators import login_required
from app.models.application_type import ApplicationType
from app.models.application_field import ApplicationField
from app.models.application import Application
from app.models.resource import Resource
from app.utils.constants import ACTION_TYPE_MODIFY

bp = Blueprint('application_multi', __name__, url_prefix='/application')


@bp.route('/multi/<int:application_type_id>/<path:resource_id>')
@login_required
def multi_record(application_type_id, resource_id):
    """複数レコード入力画面"""
    from flask import current_app
    try:
        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type:
            flash('指定された申請種類が見つかりません', 'danger')
            return redirect(url_for('application.index'))

        # 複数レコード入力をサポートしているかチェック
        if app_type.get('is_multi_record') != 'Y':
            flash('この申請種類は複数レコード入力をサポートしていません', 'danger')
            return redirect(url_for('application.index'))

        # 申請可能制限チェック
        applicant_shozoku = session.get('shozoku')
        applicant_user_id = session.get('user_id')
        if not ApplicationType.is_allowed_to_apply(app_type, applicant_shozoku, applicant_user_id):
            flash('この申請種類はあなたは申請できません', 'danger')
            return redirect(url_for('application.index'))

        # 親リソース詳細を取得
        detail_query = app_type.get('resource_detail_query')
        resource = Resource.get_resource_detail(detail_query, resource_id) if detail_query else None

        # 申請フィールドを取得
        fields = ApplicationField.get_by_application_type(application_type_id)
        current_app.logger.info(f'[multi_record] fields count: {len(fields)}')

        # 動的プルダウン用のバインド変数を準備
        applicant_user_id = session.get('user_id')
        applicant_shozoku = session.get('shozoku')
        dynamic_params = {
            'applicant_user_id': applicant_user_id,
            'applicant_shozoku': applicant_shozoku,
            'resource_id': resource_id
        }

        # プルダウンの選択肢を取得
        from app.models.admin.field_validation import FieldValidation
        for field in fields:
            # プルダウン選択肢（select と datalist 両方に対応）
            if field['field_type'] in ('select', 'datalist') and field.get('pulldown_group_id'):
                if field.get('pulldown_is_dynamic') == 'Y':
                    query = field.get('pulldown_dynamic_query')
                    if query:
                        field['options'] = ApplicationField.get_dynamic_pulldown_options(query, dynamic_params)
                else:
                    field['options'] = ApplicationField.get_pulldown_options(field['pulldown_group_id'])

        # 子レコード一覧を取得（既登録+未登録の両方）
        # resource_member_queryで既存メンバーと追加可能なレコードをis_memberフラグ付きで取得
        all_records = []
        member_query = app_type.get('resource_member_query')
        if member_query:
            user_id = session.get('user_id')
            applicant_shozoku = session.get('shozoku')
            try:
                # resource_id, applicant_user_id, applicant_shozokuを渡して、既登録メンバーと追加可能なレコードを取得
                # SQLクエリ側でis_member='Y'/'N'列を含めることを想定
                all_records = Resource.search_resources(member_query, {
                    'resource_id': resource_id,
                    'applicant_user_id': user_id,
                    'applicant_shozoku': applicant_shozoku
                })
            except Exception as e:
                current_app.logger.error(f'子レコード取得失敗: {str(e)}')
                import traceback
                current_app.logger.error(traceback.format_exc())
                all_records = []

        # 既存レコード（is_member='Y'）と未登録レコード（is_member='N'）に分ける
        existing_records = [r for r in all_records if r.get('is_member') == 'Y']

        # デバッグ: 既存レコードの最初の1件を詳細出力
        if existing_records:
            current_app.logger.info(f'[multi_record] existing_records[0] デバッグ: {existing_records[0]}')

        # record_add_mode が 'free' の場合は available_records を空にする（自由入力モード）
        if app_type.get('record_add_mode') == 'free':
            available_records = []
        else:
            available_records = [r for r in all_records if r.get('is_member') == 'N']

        current_app.logger.info(f'[multi_record] existing_records: {len(existing_records)}, available_records: {len(available_records)}')

        # 各レコードに label を追加（resource_label_column から取得）
        for record in existing_records:
            for field in fields:
                resource_col = field.get('resource_column_name')
                label_col = field.get('resource_label_column')
                if resource_col and label_col:
                    if label_col in record:
                        # _label というキーで label を保存
                        label_key = f"{resource_col}_label"
                        record[label_key] = record[label_col]

        for record in available_records:
            for field in fields:
                resource_col = field.get('resource_column_name')
                label_col = field.get('resource_label_column')
                if resource_col and label_col:
                    if label_col in record:
                        # _label というキーで label を保存
                        label_key = f"{resource_col}_label"
                        record[label_key] = record[label_col]

        return render_template('application/multi_record.html',
                               app_type=app_type,
                               fields=fields,
                               resource=resource,
                               resource_id=resource_id,
                               existing_records=existing_records,
                               available_records=available_records)
    except Exception as e:
        current_app.logger.error(f'複数レコード入力画面エラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'画面の表示に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.index'))


@bp.route('/multi/<int:application_type_id>/<path:resource_id>/submit', methods=['POST'])
@login_required
def submit_multi(application_type_id, resource_id):
    """複数レコード入力の提出処理"""
    from flask import current_app
    from app.utils.user_log import log_user_action
    try:
        user_id = session.get('user_id')
        applicant_shozoku = session.get('shozoku')

        if not applicant_shozoku:
            flash('所属が選択されていません。再度ログインしてください。', 'danger')
            return redirect(url_for('auth.login'))

        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type:
            flash('指定された申請種類が見つかりません', 'danger')
            return redirect(url_for('application.index'))

        # フィールド定義を取得（レコード補完時に使用）
        fields = ApplicationField.get_by_application_type(application_type_id)

        action = request.form.get('action')  # save_draft or submit
        current_app.logger.info(f"[submit_multi] action={action}, resource_id={resource_id}")

        # 開発中フラグのチェック（管理者以外が提出する場合）
        if action == 'submit':
            is_admin = session.get('is_admin', False)
            if not is_admin:
                if app_type and app_type.get('is_under_development') == 'Y':
                    flash('この申請種類は現在開発中のため、提出できません。下書き保存のみ可能です。', 'danger')
                    return redirect(url_for('application_multi.multi_record',
                                            application_type_id=application_type_id,
                                            resource_id=resource_id))

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

        # records[seq][field_id]形式のデータを解析（バリデーション前に実施）
        from app.models.application_detail import ApplicationDetail
        current_app.logger.info(f'[submit_multi] フォームデータ: {dict(request.form)}')
        records_data = {}
        records_labels = {}  # seq -> {field_id -> label} のマッピング

        for key, value in request.form.items():
            if key.startswith('records['):
                # records[0][action] または records[0][field_123] の形式
                # 正しくパースするために最初の]だけを区切りとする
                key_without_prefix = key.replace('records[', '', 1)  # 最初のrecords[のみ削除
                first_bracket = key_without_prefix.index(']')
                seq = int(key_without_prefix[:first_bracket])
                # 残りの部分から [field_123] を取得
                remaining = key_without_prefix[first_bracket+1:]
                if remaining.startswith('[') and remaining.endswith(']'):
                    field_key = remaining[1:-1]  # [と]を除去

                    if seq not in records_data:
                        records_data[seq] = {}
                    if seq not in records_labels:
                        records_labels[seq] = {}

                    if field_key == 'action':
                        records_data[seq]['action'] = value
                    elif field_key.startswith('field_') and field_key.endswith('_label'):
                        # labelを収集
                        field_id = int(field_key.replace('field_', '').replace('_label', ''))
                        records_labels[seq][field_id] = value
                    elif field_key.startswith('field_'):
                        field_id = int(field_key.replace('field_', ''))
                        records_data[seq][field_id] = value

        current_app.logger.info(f'[submit_multi] 解析されたレコード数: {len(records_data)}')
        current_app.logger.info(f'[submit_multi] records_data: {records_data}')

        # 既存レコードのis_updatableをチェック用に取得
        all_records = []
        member_query = app_type.get('resource_member_query')
        if member_query:
            try:
                all_records = Resource.search_resources(member_query, {
                    'resource_id': resource_id,
                    'applicant_user_id': user_id,
                    'applicant_shozoku': applicant_shozoku
                })
            except Exception as e:
                current_app.logger.warning(f'レコード検証用取得失敗: {str(e)}')

        existing_records = [r for r in all_records if r.get('is_member') == 'Y']
        updatable_map = {i+1: r.get('is_updatable', 'Y') for i, r in enumerate(existing_records)}

        # まず下書きとして保存（バリデーションエラー時に入力値を保持するため）
        application_data = {
            'application_type_id': application_type_id,
            'action_type': ACTION_TYPE_MODIFY,  # 複数レコード入力は基本的にmodify扱い
            'applicant_user_id': user_id,
            'applicant_shozoku': applicant_shozoku,
            'jurisdiction_shozoku': jurisdiction_shozoku,
            'application_title': request.form.get('application_title'),
            'resource_id': resource_id,
            'remarks': request.form.get('remarks')
        }

        # 申請を作成
        application_id = Application.create(application_data)

        # 各レコードを保存（全アクションを保存、編集画面で元データを復元するため）
        field_values = []
        detail_seq_counter = 1  # detail_seqは1から連番

        # 既存レコードのマップ（seq -> レコードデータ）を作成
        existing_records_map = {i+1: r for i, r in enumerate(existing_records)}

        # キーフィールドの重複チェック
        key_fields = [f for f in fields if f.get('is_key_field') == 'Y']
        if key_fields:
            active_records = {}
            for seq, record in records_data.items():
                record_action = record.get('action', 'add')
                if record_action != 'delete':  # 削除予定を除外
                    key_values = tuple(record.get(f['field_id'], '') for f in key_fields)
                    # すべてのキーフィールドが空でない場合のみチェック
                    if all(key_values):
                        if key_values in active_records:
                            key_field_names = ', '.join(f['field_name'] for f in key_fields)
                            flash(f'キーフィールド（{key_field_names}）の組み合わせが重複しています。', 'danger')
                            return redirect(url_for('application_multi.multi_record',
                                                    application_type_id=application_type_id,
                                                    resource_id=resource_id))
                        active_records[key_values] = seq

        for seq, record in records_data.items():
            record_action = record.get('action', 'add')

            # サーバー側検証: is_updatable='N'のレコードの変更を拒否
            if seq in updatable_map and updatable_map[seq] == 'N':
                if record_action not in ['none', 'readonly']:
                    current_app.logger.warning(f'更新不可レコード(seq={seq})への不正な操作を拒否: {record_action}')
                    continue

            # サーバー側検証: support_modify='N'の場合はmodifyアクションを拒否
            if record_action == 'modify' and app_type.get('support_modify') != 'Y':
                current_app.logger.warning(f'support_modify=Nの申請種類でmodifyアクションを拒否: seq={seq}')
                flash('この申請種類は修正アクションをサポートしていません', 'danger')
                return redirect(url_for('application_multi.multi_record',
                                        application_type_id=application_type_id,
                                        resource_id=resource_id))

            # 既存レコードの場合（add以外）、フォームで送信されなかったフィールドを元のリソースデータから補完
            if record_action != 'add' and seq in existing_records_map:
                existing_data = existing_records_map[seq]
                for field in fields:
                    field_id = field['field_id']
                    # フォームに存在しないフィールドを既存データから補完
                    if field_id not in record:
                        column_name = field.get('resource_column_name')
                        if column_name and column_name in existing_data:
                            value = existing_data[column_name]
                            # 値を文字列に変換（数値型の場合に対応）
                            if value is not None and not isinstance(value, str):
                                value = str(value)
                            record[field_id] = value
                            current_app.logger.info(f'[submit_multi] レコード{seq}(action={record_action})のfield_id={field_id}を元のリソースデータから補完')

            for field_id, field_value in record.items():
                if field_id != 'action':
                    # labelを取得（フォームから送信されたもの、またはリソースデータから）
                    field_label = records_labels.get(seq, {}).get(field_id)

                    # フォームにlabelがない場合、既存レコードからlabelを取得
                    if not field_label and record_action != 'add' and seq in existing_records_map:
                        existing_data = existing_records_map[seq]
                        # 対応するfieldを探す
                        field_def = next((f for f in fields if f['field_id'] == field_id), None)
                        if field_def and field_def.get('resource_label_column'):
                            label_column = field_def['resource_label_column']
                            if label_column in existing_data:
                                field_label = existing_data[label_column]
                                current_app.logger.info(f'[submit_multi] レコード{seq}のfield_id={field_id}にlabelを補完（リソースデータ）: {field_label}')

                    # まだlabelがない場合、プルダウンフィールドならoption_labelを取得
                    if not field_label and field_value:
                        field_def = next((f for f in fields if f['field_id'] == field_id), None)
                        if field_def and field_def['field_type'] in ('select', 'datalist'):
                            # プルダウンの選択肢からlabelを取得
                            if field_def.get('pulldown_group_id'):
                                dynamic_params = {
                                    'applicant_user_id': user_id,
                                    'applicant_shozoku': applicant_shozoku,
                                    'resource_id': resource_id
                                }
                                if field_def.get('pulldown_is_dynamic') == 'Y':
                                    query = field_def.get('pulldown_dynamic_query')
                                    if query:
                                        options = ApplicationField.get_dynamic_pulldown_options(query, dynamic_params)
                                        matching_option = next((opt for opt in options if str(opt.get('option_value')) == str(field_value)), None)
                                        if matching_option:
                                            field_label = matching_option.get('option_label')
                                            current_app.logger.info(f'[submit_multi] レコード{seq}のfield_id={field_id}にlabelを補完（動的プルダウン）: {field_label}')
                                else:
                                    options = ApplicationField.get_pulldown_options(field_def['pulldown_group_id'])
                                    matching_option = next((opt for opt in options if str(opt.get('option_value')) == str(field_value)), None)
                                    if matching_option:
                                        field_label = matching_option.get('option_label')
                                        current_app.logger.info(f'[submit_multi] レコード{seq}のfield_id={field_id}にlabelを補完（静的プルダウン）: {field_label}')

                    field_values.append({
                        'detail_seq': detail_seq_counter,
                        'field_id': field_id,
                        'field_value': field_value,
                        'field_label': field_label,
                        'detail_action': record_action
                    })

            detail_seq_counter += 1

        current_app.logger.info(f"[submit_multi] field_values type: {type(field_values)}")
        current_app.logger.info(f"[submit_multi] field_values count: {len(field_values) if isinstance(field_values, list) else 'NOT A LIST'}")
        if field_values:
            if isinstance(field_values, list):
                current_app.logger.info(f"[submit_multi] 保存するfield_values: {field_values[:5]}...")
                ApplicationDetail.save_details(application_id, field_values)
            else:
                current_app.logger.error(f"[submit_multi] field_valuesがリストではありません: {field_values}")
                raise TypeError(f"field_valuesはリストである必要がありますが、{type(field_values)}でした")
        else:
            current_app.logger.warning(f"[submit_multi] field_valuesが空です！")

        # バリデーション実行（申請提出時のみ）
        if action == 'submit':
            from app.services.validation_service import ValidationService
            validation_errors = []
            field_map = {f['field_id']: f for f in fields}

            for seq, record in records_data.items():
                record_action = record.get('action', 'add')

                # add と modify のレコードのみバリデーション
                if record_action in ['add', 'modify']:
                    for field_id, field_value in record.items():
                        if field_id != 'action' and field_id in field_map:
                            field = field_map[field_id]

                            # 操作タイプを決定（addならcreate、modifyならmodify）
                            operation_type = 'create' if record_action == 'add' else 'modify'

                            # バリデーション実行
                            # 注：複数レコードの場合、キー項目は既存が変更不可、新規は未登録からのみ選択可能なため
                            # unique_in_table系の重複チェックは不要
                            is_valid, errors = ValidationService.validate_field(
                                field_id=field_id,
                                value=field_value,
                                operation_type=operation_type,
                                resource_id=resource_id
                            )

                            if not is_valid and errors:
                                for error in errors:
                                    validation_errors.append(f'レコード{seq} - {field["field_name"]}: {error}')

            # バリデーションエラーがあれば下書き編集画面へ
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'danger')
                return redirect(url_for('application_multi.edit_multi_record',
                                        application_id=application_id,
                                        application_type_id=application_type_id,
                                        resource_id=resource_id))

            # バリデーションが通った場合は承認者選択画面へ（提出ログはconfirm_approvers内で記録）
            return redirect(url_for('application.select_approvers', application_id=application_id))
        else:
            # 下書き保存のみの場合
            application_type_code = app_type.get('application_type_code') if app_type else None
            log_user_action(user_id, 'save_draft', application_id, application_type_code)
            flash(f'下書きとして保存しました（申請ID: {application_id}）', 'success')
            return redirect(url_for('application.list'))

    except Exception as e:
        current_app.logger.error(f'複数レコード申請の提出に失敗: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'申請の提出に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application_multi.multi_record',
                                application_type_id=application_type_id,
                                resource_id=resource_id))


@bp.route('/edit/<int:application_id>/<int:application_type_id>/<path:resource_id>')
@login_required
def edit_multi_record(application_id, application_type_id, resource_id):
    """複数レコード申請の編集画面（下書きから再編集）"""
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
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type:
            flash('指定された申請種類が見つかりません', 'danger')
            return redirect(url_for('application.index'))

        # 複数レコード入力をサポートしているかチェック
        if app_type.get('is_multi_record') != 'Y':
            flash('この申請種類は複数レコード入力をサポートしていません', 'danger')
            return redirect(url_for('application.index'))

        # 申請可能制限チェック
        applicant_shozoku = session.get('shozoku')
        applicant_user_id = session.get('user_id')
        if not ApplicationType.is_allowed_to_apply(app_type, applicant_shozoku, applicant_user_id):
            flash('この申請種類はあなたは申請できません', 'danger')
            return redirect(url_for('application.index'))

        # 親リソース詳細を取得
        detail_query = app_type.get('resource_detail_query')
        resource = Resource.get_resource_detail(detail_query, resource_id) if detail_query else None

        # 申請フィールドを取得
        fields = ApplicationField.get_by_application_type(application_type_id)

        # 動的プルダウン用のバインド変数を準備
        applicant_user_id = session.get('user_id')
        dynamic_params = {
            'applicant_user_id': applicant_user_id,
            'applicant_shozoku': applicant_shozoku,
            'resource_id': resource_id
        }

        # プルダウンの選択肢を取得
        for field in fields:
            if field['field_type'] in ('select', 'datalist') and field.get('pulldown_group_id'):
                if field.get('pulldown_is_dynamic') == 'Y':
                    query = field.get('pulldown_dynamic_query')
                    if query:
                        field['options'] = ApplicationField.get_dynamic_pulldown_options(query, dynamic_params)
                else:
                    field['options'] = ApplicationField.get_pulldown_options(field['pulldown_group_id'])

        # 既存の申請詳細を取得してレコード形式に復元
        from app.models.application_detail import ApplicationDetail
        existing_details = ApplicationDetail.get_by_application(application_id)

        # detail_seqでグループ化してレコード形式に変換
        existing_records = []
        records_by_seq = {}

        current_app.logger.info(f'[edit_multi_record] existing_details count: {len(existing_details)}')

        for detail in existing_details:
            seq = detail['detail_seq']
            if seq not in records_by_seq:
                action = detail.get('detail_action', 'none')
                # readonly アクションのレコードのみ編集不可
                is_updatable = 'N' if action == 'readonly' else 'Y'
                records_by_seq[seq] = {
                    'action': action,
                    'is_updatable': is_updatable
                }
            # field_id をキーとして値を格納（resource_column_name は使わない）
            records_by_seq[seq][detail['field_id']] = detail['field_value']
            # field_label も格納（あれば）
            if detail.get('field_label'):
                label_key = f"{detail['field_id']}_label"
                records_by_seq[seq][label_key] = detail['field_label']
                current_app.logger.info(f'[edit_multi_record] seq={seq}, field_id={detail["field_id"]}, value={detail["field_value"]}, label={detail["field_label"]}')
            else:
                current_app.logger.info(f'[edit_multi_record] seq={seq}, field_id={detail["field_id"]}, value={detail["field_value"]}')

        # records_by_seqをリスト形式に変換
        for seq in sorted(records_by_seq.keys()):
            existing_records.append(records_by_seq[seq])

        # 未登録レコード一覧を取得（追加用）
        available_records = []

        # record_add_mode が 'free' の場合は available_records を空にする（自由入力モード）
        if app_type.get('record_add_mode') == 'free':
            current_app.logger.info(f'[edit_multi_record] record_add_mode=free: 自由入力モード')
            available_records = []
        else:
            member_query = app_type.get('resource_member_query')
            if member_query:
                user_id = session.get('user_id')
                applicant_shozoku = session.get('shozoku')
                try:
                    all_records = Resource.search_resources(member_query, {
                        'resource_id': resource_id,
                        'applicant_user_id': user_id,
                        'applicant_shozoku': applicant_shozoku
                    })
                    # 未登録レコードのみを抽出
                    available_records = [r for r in all_records if r.get('is_member') == 'N']
                    current_app.logger.info(f'[edit_multi_record] record_add_mode=select: 候補選択モード, available: {len(available_records)}')
                except Exception as e:
                    current_app.logger.error(f'子レコード取得失敗: {str(e)}')
                    available_records = []

        return render_template('application/multi_record_edit.html',
                               application=application,
                               app_type=app_type,
                               fields=fields,
                               resource=resource,
                               resource_id=resource_id,
                               existing_records=existing_records,
                               available_records=available_records)

    except Exception as e:
        current_app.logger.error(f'複数レコード編集画面エラー: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'編集画面の表示に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application.list'))


@bp.route('/edit/<int:application_id>/<int:application_type_id>/<path:resource_id>/submit', methods=['POST'])
@login_required
def submit_edit_multi(application_id, application_type_id, resource_id):
    """複数レコード申請の編集保存処理"""
    from flask import current_app
    from app.utils.user_log import log_user_action
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

        # 申請種類を取得
        app_type = ApplicationType.get_by_id(application_type_id)
        if not app_type:
            flash('指定された申請種類が見つかりません', 'danger')
            return redirect(url_for('application.index'))

        action = request.form.get('action')  # save_draft or submit
        current_app.logger.info(f'[submit_edit_multi] action={action}, application_id={application_id}')
        current_app.logger.info(f'[submit_edit_multi] フォームパラメータキー: {list(request.form.keys())}')

        # 開発中フラグのチェック（管理者以外が提出する場合）
        if action == 'submit':
            is_admin = session.get('is_admin', False)
            if not is_admin:
                if app_type and app_type.get('is_under_development') == 'Y':
                    flash('この申請種類は現在開発中のため、提出できません。下書き保存のみ可能です。', 'danger')
                    return redirect(url_for('application_multi.edit_multi_record',
                                            application_id=application_id,
                                            application_type_id=application_type_id,
                                            resource_id=resource_id))

        # 申請タイトルと備考を更新
        from app.utils.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE T_APPLICATION
            SET application_title = :application_title,
                remarks = :remarks,
                updated_at = SYSTIMESTAMP
            WHERE application_id = :application_id
        """
        cursor.execute(sql, {
            'application_id': application_id,
            'application_title': request.form.get('application_title'),
            'remarks': request.form.get('remarks')
        })
        conn.commit()
        cursor.close()

        # records[seq][field_id]形式のデータを解析
        current_app.logger.info(f'[submit_edit_multi] フォームデータ: {dict(request.form)}')
        records_data = {}
        records_labels = {}  # seq -> {field_id -> label} のマッピング

        for key, value in request.form.items():
            if key.startswith('records['):
                # records[0][action] または records[0][field_123] の形式
                # 正しくパースするために最初の]だけを区切りとする
                key_without_prefix = key.replace('records[', '', 1)  # 最初のrecords[のみ削除
                first_bracket = key_without_prefix.index(']')
                seq = int(key_without_prefix[:first_bracket])
                # 残りの部分から [field_123] を取得
                remaining = key_without_prefix[first_bracket+1:]
                if remaining.startswith('[') and remaining.endswith(']'):
                    field_key = remaining[1:-1]  # [と]を除去

                    if seq not in records_data:
                        records_data[seq] = {}
                    if seq not in records_labels:
                        records_labels[seq] = {}

                    if field_key == 'action':
                        records_data[seq]['action'] = value
                    elif field_key.startswith('field_') and field_key.endswith('_label'):
                        # labelを収集
                        field_id = int(field_key.replace('field_', '').replace('_label', ''))
                        records_labels[seq][field_id] = value
                    elif field_key.startswith('field_'):
                        field_id = int(field_key.replace('field_', ''))
                        records_data[seq][field_id] = value

        current_app.logger.info(f'[submit_edit_multi] 解析されたレコード数: {len(records_data)}')
        current_app.logger.info(f'[submit_edit_multi] records_data: {records_data}')

        # フィールド定義を取得（キーフィールドチェック用）
        fields = ApplicationField.get_by_application_type(application_type_id)

        # 動的プルダウン用のバインド変数を準備
        dynamic_params = {
            'applicant_user_id': user_id,
            'applicant_shozoku': applicant_shozoku,
            'resource_id': resource_id
        }

        # キーフィールドの重複チェック
        key_fields = [f for f in fields if f.get('is_key_field') == 'Y']
        if key_fields:
            active_records = {}
            for seq, record in records_data.items():
                record_action = record.get('action', 'none')
                if record_action != 'delete':  # 削除予定を除外
                    key_values = tuple(record.get(f['field_id'], '') for f in key_fields)
                    # すべてのキーフィールドが空でない場合のみチェック
                    if all(key_values):
                        if key_values in active_records:
                            key_field_names = ', '.join(f['field_name'] for f in key_fields)
                            flash(f'キーフィールド（{key_field_names}）の組み合わせが重複しています。', 'danger')
                            return redirect(url_for('application_multi.edit_multi_record',
                                                    application_id=application_id,
                                                    application_type_id=application_type_id,
                                                    resource_id=resource_id))
                        active_records[key_values] = seq

        # 既存の申請詳細を取得（補完用）
        from app.models.application_detail import ApplicationDetail
        existing_details = ApplicationDetail.get_by_application(application_id)

        # detail_seqでグループ化
        existing_records_by_seq = {}
        for detail in existing_details:
            seq = detail['detail_seq']
            if seq not in existing_records_by_seq:
                existing_records_by_seq[seq] = {}
            existing_records_by_seq[seq][detail['field_id']] = detail['field_value']
            # field_label も保存
            if detail.get('field_label'):
                label_key = f"{detail['field_id']}_label"
                existing_records_by_seq[seq][label_key] = detail['field_label']

        # 各レコードを保存（全アクションを保存）
        field_values = []
        detail_seq_counter = 1  # detail_seqは1から連番

        for seq, record in records_data.items():
            record_action = record.get('action', 'add')

            # サーバー側検証: support_modify='N'の場合はmodifyアクションを拒否
            if record_action == 'modify' and app_type.get('support_modify') != 'Y':
                current_app.logger.warning(f'support_modify=Nの申請種類でmodifyアクションを拒否（編集保存）: seq={seq}')
                flash('この申請種類は修正アクションをサポートしていません', 'danger')
                return redirect(url_for('application_multi.edit_multi_record',
                                        application_id=application_id,
                                        application_type_id=application_type_id,
                                        resource_id=resource_id))

            # 既存レコードの場合（add以外）、フォームで送信されなかったフィールドを既存データから補完
            if record_action != 'add' and seq in existing_records_by_seq:
                existing_data = existing_records_by_seq[seq]
                for field in fields:
                    field_id = field['field_id']
                    # フォームに存在しないフィールドを既存データから補完
                    if field_id not in record and field_id in existing_data:
                        value = existing_data[field_id]
                        # 値を文字列に変換（数値型の場合に対応）
                        if value is not None and not isinstance(value, str):
                            value = str(value)
                        record[field_id] = value
                        current_app.logger.info(f'[submit_edit_multi] レコード{seq}(action={record_action})のfield_id={field_id}を既存データから補完')

            for field_id, field_value in record.items():
                if field_id != 'action':
                    # labelを取得（フォームから送信されたもの、または既存データから）
                    field_label = records_labels.get(seq, {}).get(field_id)

                    # フォームにlabelがない場合、既存レコードのlabelを使用
                    if not field_label and record_action != 'add' and seq in existing_records_by_seq:
                        label_key = f"{field_id}_label"
                        if label_key in existing_records_by_seq[seq]:
                            field_label = existing_records_by_seq[seq][label_key]
                            current_app.logger.info(f'[submit_edit_multi] レコード{seq}のfield_id={field_id}にlabelを補完（既存データ）: {field_label}')

                    # まだlabelがない場合、プルダウンフィールドならoption_labelを取得
                    if not field_label and field_value:
                        field_def = next((f for f in fields if f['field_id'] == field_id), None)
                        if field_def and field_def['field_type'] in ('select', 'datalist'):
                            # プルダウンの選択肢からlabelを取得
                            if field_def.get('pulldown_group_id'):
                                if field_def.get('pulldown_is_dynamic') == 'Y':
                                    query = field_def.get('pulldown_dynamic_query')
                                    if query:
                                        options = ApplicationField.get_dynamic_pulldown_options(query, dynamic_params)
                                        matching_option = next((opt for opt in options if str(opt.get('option_value')) == str(field_value)), None)
                                        if matching_option:
                                            field_label = matching_option.get('option_label')
                                            current_app.logger.info(f'[submit_edit_multi] レコード{seq}のfield_id={field_id}にlabelを補完（動的プルダウン）: {field_label}')
                                else:
                                    options = ApplicationField.get_pulldown_options(field_def['pulldown_group_id'])
                                    matching_option = next((opt for opt in options if str(opt.get('option_value')) == str(field_value)), None)
                                    if matching_option:
                                        field_label = matching_option.get('option_label')
                                        current_app.logger.info(f'[submit_edit_multi] レコード{seq}のfield_id={field_id}にlabelを補完（静的プルダウン）: {field_label}')

                    field_values.append({
                        'detail_seq': detail_seq_counter,
                        'field_id': field_id,
                        'field_value': field_value,
                        'field_label': field_label,
                        'detail_action': record_action
                    })

            detail_seq_counter += 1

        current_app.logger.info(f"[submit_edit_multi] field_values type: {type(field_values)}")
        current_app.logger.info(f"[submit_edit_multi] field_values count: {len(field_values) if isinstance(field_values, list) else 'NOT A LIST'}")

        # 既存の申請詳細を削除
        ApplicationDetail.delete_by_application(application_id)

        # 新しいデータを保存
        if field_values:
            if isinstance(field_values, list):
                current_app.logger.info(f"[submit_edit_multi] 保存するfield_values: {field_values[:5]}...")
                ApplicationDetail.save_details(application_id, field_values)
            else:
                current_app.logger.error(f"[submit_edit_multi] field_valuesがリストではありません: {field_values}")
                raise TypeError(f"field_valuesはリストである必要がありますが、{type(field_values)}でした")
        else:
            current_app.logger.warning(f"[submit_edit_multi] field_valuesが空です！")

        # バリデーション実行（申請提出時のみ）
        if action == 'submit':
            from app.services.validation_service import ValidationService
            validation_errors = []
            field_map = {f['field_id']: f for f in fields}

            for seq, record in records_data.items():
                record_action = record.get('action', 'add')

                # add と modify のレコードのみバリデーション
                if record_action in ['add', 'modify']:
                    for field_id, field_value in record.items():
                        if field_id != 'action' and field_id in field_map:
                            field = field_map[field_id]

                            # 操作タイプを決定（addならcreate、modifyならmodify）
                            operation_type = 'create' if record_action == 'add' else 'modify'

                            # バリデーション実行
                            is_valid, errors = ValidationService.validate_field(
                                field_id=field_id,
                                value=field_value,
                                operation_type=operation_type,
                                resource_id=resource_id
                            )

                            if not is_valid and errors:
                                for error in errors:
                                    validation_errors.append(f'レコード{seq} - {field["field_name"]}: {error}')

            # バリデーションエラーがあれば下書き編集画面へ
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'danger')
                return redirect(url_for('application_multi.edit_multi_record',
                                        application_id=application_id,
                                        application_type_id=application_type_id,
                                        resource_id=resource_id))

            # バリデーションが通った場合は承認者選択画面へ（提出ログはconfirm_approvers内で記録）
            return redirect(url_for('application.select_approvers', application_id=application_id))
        else:
            # 下書き保存のみの場合
            application_type_code = app_type.get('application_type_code') if app_type else None
            log_user_action(user_id, 'save_draft', application_id, application_type_code)
            flash(f'下書きとして保存しました（申請ID: {application_id}）', 'success')
            return redirect(url_for('application.list'))

    except Exception as e:
        current_app.logger.error(f'複数レコード申請の編集保存に失敗: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'申請の保存に失敗しました: {str(e)}', 'danger')
        return redirect(url_for('application_multi.edit_multi_record',
                                application_id=application_id,
                                application_type_id=application_type_id,
                                resource_id=resource_id))
