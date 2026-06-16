"""
Flaskアプリケーションファクトリ
"""
from flask import Flask, render_template
from app.utils.db import init_db


def create_app(config_name=None):
    """
    Flaskアプリケーションを作成

    Args:
        config_name: 設定名（development/staging/production/testing）
                     Noneの場合は環境変数DEPLOYMENT_SLOTから自動判定

    Returns:
        Flask: Flaskアプリケーションインスタンス
    """
    import os

    app = Flask(__name__)

    # 設定読み込み（環境変数から自動判定）
    if config_name is None:
        deployment_slot = os.environ.get('DEPLOYMENT_SLOT', 'development')
        config_name = deployment_slot

    if config_name == 'development':
        from app.config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    elif config_name == 'staging':
        from app.config import StagingConfig
        app.config.from_object(StagingConfig)
    elif config_name == 'production':
        from app.config import ProductionConfig
        app.config.from_object(ProductionConfig)
    elif config_name == 'testing':
        from app.config import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        from app.config import Config
        app.config.from_object(Config)

    # 仮想ディレクトリ対応：環境変数からアプリケーションルートパスを取得
    # 例: APPLICATION_ROOT=/workflow を設定すると https://server/workflow/ 配下で動作
    application_root = os.environ.get('APPLICATION_ROOT', '/')
    if application_root != '/':
        app.config['APPLICATION_ROOT'] = application_root
        app.logger.info(f'Application root set to: {application_root}')

    # データベース初期化
    init_db(app)

    # Blueprintを登録
    from app.routes import auth, application, application_modify, application_multi, approval, admin, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(application.bp)
    app.register_blueprint(application_modify.bp)
    app.register_blueprint(application_multi.bp)
    app.register_blueprint(approval.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)

    # ルートパスのハンドラー
    @app.route('/')
    def index():
        """ルートパス - ログインまたは申請一覧へリダイレクト"""
        from flask import session, redirect, url_for
        if session.get('user_id'):
            return redirect(url_for('application.list'))
        else:
            return redirect(url_for('auth.login'))

    # エラーハンドラー登録
    register_error_handlers(app)

    # テンプレートフィルター登録
    register_template_filters(app)

    # コンテキストプロセッサー登録
    register_context_processors(app)

    return app


def register_error_handlers(app):
    """エラーハンドラーを登録"""

    @app.errorhandler(400)
    def bad_request(error):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f'Server Error: {error}')
        return render_template('errors/500.html'), 500


def register_template_filters(app):
    """テンプレートフィルターを登録"""
    from app.utils.helpers import format_date, format_status, format_action_type
    from app.utils.text_formatter import format_help_text

    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_status'] = format_status
    app.jinja_env.filters['format_action_type'] = format_action_type
    app.jinja_env.filters['format_help_text'] = format_help_text


def register_context_processors(app):
    """コンテキストプロセッサーを登録"""
    from flask import session

    @app.context_processor
    def inject_common_variables():
        """すべてのテンプレートで使用可能な変数を注入"""
        pending_count = 0

        # ログイン済みの場合、承認待ちタスク数を取得
        if session.get('user_id'):
            try:
                from app.services.approval_service import ApprovalService
                _, pending_count = ApprovalService.get_pending_tasks_count(
                    session.get('user_id')
                )
            except Exception:
                pending_count = 0

        return {
            'pending_count': pending_count,
            'session': session
        }
