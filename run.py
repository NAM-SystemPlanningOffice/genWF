"""
開発サーバー起動スクリプト
"""
import os
from app import create_app

# 環境変数から設定を読み込み
config_name = os.environ.get('FLASK_ENV', 'development')

# アプリケーションを作成
app = create_app(config_name)

if __name__ == '__main__':
    # 開発サーバーを起動
    # host='127.0.0.1' でローカルホストのみリッスン（Windows Firewall警告回避）
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=(config_name == 'development')
    )
