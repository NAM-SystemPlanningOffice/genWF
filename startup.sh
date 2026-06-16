#!/bin/bash
# Azure App Service起動スクリプト
# Gunicornを使用してFlaskアプリケーションを起動

# 環境変数の確認（デバッグ用）
echo "DEPLOYMENT_SLOT: $DEPLOYMENT_SLOT"
echo "ORACLE_DSN: $ORACLE_DSN"

# Gunicornでアプリケーションを起動
# - app:create_app() でアプリケーションファクトリを呼び出し
# - DEPLOYMENT_SLOT環境変数に基づいて自動的に設定が選択される
exec gunicorn --config gunicorn_config.py "app:create_app()"
