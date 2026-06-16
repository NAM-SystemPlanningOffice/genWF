"""
Gunicorn設定ファイル（Azure App Service用）
"""
import multiprocessing
import os

# バインドアドレス（App ServiceはポートをPORT環境変数で渡す）
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# ワーカープロセス数（CPU数 * 2 + 1 が推奨）
workers = multiprocessing.cpu_count() * 2 + 1

# ワーカークラス（同期ワーカー）
worker_class = "sync"

# タイムアウト設定（秒）
timeout = 120

# キープアライブ（秒）
keepalive = 5

# ログレベル
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# アクセスログ
accesslog = "-"  # 標準出力

# エラーログ
errorlog = "-"  # 標準エラー出力

# プロセス名
proc_name = "genWF"

# リクエスト処理前にpythonpathを追加（必要に応じて）
pythonpath = os.environ.get('PYTHONPATH', '')

# preload: アプリケーションをマスタープロセスでロード（メモリ効率化）
preload_app = True

# 最大リクエストサイズ（デフォルト無制限だが安全のため設定）
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190
