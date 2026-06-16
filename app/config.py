"""
アプリケーション設定
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


class Config:
    """基本設定"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # セッション設定
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'flask_session'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Oracle DB接続設定（python-oracledb）
    ORACLE_DSN = os.environ.get('ORACLE_DSN')
    ORACLE_USER = os.environ.get('ORACLE_USER')
    ORACLE_PASSWORD = os.environ.get('ORACLE_PASSWORD')
    # python-oracledb はデフォルトでUTF-8を使用するため、encoding指定は不要

    # アプリケーション設定
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))
    MAX_UPLOAD_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', 10 * 1024 * 1024))

    # ログ設定
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')


class DevelopmentConfig(Config):
    """開発環境設定"""
    DEBUG = True
    TESTING = False


class StagingConfig(Config):
    """Staging環境設定（App Service stagingスロット）"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'INFO'


class ProductionConfig(Config):
    """本番環境設定（App Service productionスロット）"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    """テスト環境設定"""
    TESTING = True
    DEBUG = True
    # テスト用のDB接続先を設定
    ORACLE_DSN = os.environ.get('TEST_ORACLE_DSN', Config.ORACLE_DSN)
