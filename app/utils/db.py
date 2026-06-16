"""
データベース接続管理
Python 3.13対応 - oracledb (python-oracledb) 使用
"""
import os
from flask import current_app, g


def init_db(app):
    """
    データベース接続の初期化

    Args:
        app: Flaskアプリケーション
    """
    # モックDB使用フラグのチェック
    use_mock = os.environ.get('USE_MOCK_DB', 'False').lower() == 'true'

    if use_mock:
        app.logger.info("Using Mock Database (for testing without Oracle DB)")
        return

    try:
        import oracledb

        # Thick modeを使用する場合（Oracle Instant Client必要）
        # use_thick = os.environ.get('USE_THICK_MODE', 'False').lower() == 'true'
        # if use_thick:
        #     oracledb.init_oracle_client(lib_dir="C:/oracle/instantclient_19_XX")
        #     app.logger.info("Oracle DB: Using Thick mode (with Oracle Client)")
        # else:
        #     app.logger.info("Oracle DB: Using Thin mode (pure Python, no Oracle Client needed)")

        app.logger.info("Oracle DB: Using python-oracledb (Thin mode by default)")

    except ImportError:
        app.logger.warning("oracledb not installed. Install it with: pip install oracledb")
    except Exception as e:
        app.logger.warning(f"Oracle DB initialization: {e}")


def get_db_connection():
    """
    データベース接続を取得

    Returns:
        oracledb.Connection or MockConnection: データベース接続
    """
    # モックDB使用フラグのチェック
    use_mock_env = os.environ.get('USE_MOCK_DB', 'False')
    use_mock = use_mock_env.lower() == 'true'

    if use_mock:
        from app.utils.db_mock import get_mock_db_connection
        return get_mock_db_connection()

    # 通常のOracle接続
    if 'db' not in g:
        import oracledb
        from flask import current_app

        dsn = current_app.config['ORACLE_DSN']
        user = current_app.config['ORACLE_USER']
        password = current_app.config['ORACLE_PASSWORD']

        try:
            # python-oracledb での接続
            g.db = oracledb.connect(
                user=user,
                password=password,
                dsn=dsn
            )
            current_app.logger.debug(f"Connected to Oracle DB: {dsn}")

        except oracledb.Error as e:
            current_app.logger.error(f"Database connection error: {e}")
            raise

    return g.db


def close_db_connection(e=None):
    """
    データベース接続をクローズ

    Args:
        e: エラー情報（オプション）
    """
    db = g.pop('db', None)

    if db is not None:
        db.close()


def dict_factory(cursor):
    """
    カーソルの結果を辞書形式に変換するファクトリ関数

    Args:
        cursor: cx_Oracle.Cursor

    Returns:
        list: 辞書のリスト
    """
    columns = [col[0].lower() for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def dict_fetchone(cursor):
    """
    カーソルの結果1行を辞書形式で取得

    Args:
        cursor: cx_Oracle.Cursor

    Returns:
        dict: 1行分のデータ（辞書形式）
    """
    row = cursor.fetchone()
    if row:
        columns = [col[0].lower() for col in cursor.description]
        return dict(zip(columns, row))
    return None
