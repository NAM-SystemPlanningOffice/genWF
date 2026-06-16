"""
認証関連のルーティング
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン画面"""
    from flask import current_app
    from app.utils.auth import get_authenticated_user_from_request
    import os

    # 環境判定: DEPLOYMENT_SLOT変数で判断
    deployment_slot = os.environ.get('DEPLOYMENT_SLOT', 'development')
    is_production = deployment_slot in ('staging', 'production')

    # staging/production環境: Entra ID Easy AuthからユーザーIDを取得
    if is_production:
        # Entra ID Easy Auth (X-MS-CLIENT-PRINCIPAL-NAME) からユーザーIDを取得
        user_id = get_authenticated_user_from_request(request)

        if user_id:
            current_app.logger.info(f'[login] Entra ID認証成功: user_id={user_id} (slot={deployment_slot})')
        else:
            current_app.logger.error(f'[login] Entra ID認証失敗: ユーザーIDが取得できません (slot={deployment_slot})')
            current_app.logger.debug(f'[login] Headers: {dict(request.headers)}')
            flash('認証に失敗しました。システム管理者に連絡してください。', 'danger')
            return render_template('auth/login.html', sso_mode=True)

    # 開発環境: フォームからユーザーIDを入力
    else:
        if request.method == 'POST':
            user_id = request.form.get('user_id')
        else:
            # GET時はログイン画面を表示
            return render_template('auth/login.html', sso_mode=False)

    # ユーザーIDが取得できた場合、認証処理を実行
    if user_id:
        from app.models.user import User

        # ユーザー情報を取得
        user = User.get_by_id(user_id)
        if user:
            # セッションに基本情報を保存
            session['user_id'] = user_id
            session['user_name'] = user['user_name']

            # 管理者かどうかをチェック
            from app.models.admin_user import AdminUser
            try:
                is_admin = AdminUser.is_admin(user_id)
                session['is_admin'] = is_admin
                current_app.logger.info(f'[login] user_id={user_id}, is_admin={is_admin}')
            except Exception as e:
                current_app.logger.error(f'[login] 管理者チェックエラー: {str(e)}')
                import traceback
                current_app.logger.error(traceback.format_exc())
                session['is_admin'] = False

            # 所属選択画面へ
            flash('ログインしました', 'success')
            return redirect(url_for('auth.select_department'))
        else:
            flash('ユーザーが見つかりません', 'danger')
            deployment_slot = os.environ.get('DEPLOYMENT_SLOT', 'development')
            is_production = deployment_slot in ('staging', 'production')
            return render_template('auth/login.html', sso_mode=is_production)
    else:
        # 開発環境でユーザーIDが未入力の場合
        if not is_production:
            flash('ユーザーIDを入力してください', 'danger')

    return render_template('auth/login.html', sso_mode=is_production)


@bp.route('/select-department', methods=['GET', 'POST'])
def select_department():
    """所属選択画面"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    from app.models.user import User

    if request.method == 'POST':
        shozoku = request.form.get('shozoku')
        shozoku_name = request.form.get('shozoku_name')

        if shozoku:
            session['shozoku'] = shozoku
            session['shozoku_name'] = shozoku_name
            flash(f'所属を選択しました: {shozoku_name}', 'success')
            return redirect(url_for('application.list'))
        else:
            flash('所属を選択してください', 'danger')

    # ユーザーの所属一覧を取得
    departments = User.get_user_departments(user_id)

    # 所属が1つしかない場合は自動的に選択してスキップ
    if len(departments) == 1:
        dept = departments[0]
        session['shozoku'] = dept['shozoku']
        session['shozoku_name'] = dept['shozoku_name']
        flash(f'所属を選択しました: {dept["shozoku_name"]}', 'success')
        return redirect(url_for('application.list'))

    return render_template('auth/select_department.html', departments=departments)


@bp.route('/logout')
def logout():
    """ログアウト"""
    session.clear()
    flash('ログアウトしました', 'info')
    return redirect(url_for('auth.login'))
