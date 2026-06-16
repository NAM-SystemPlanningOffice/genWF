@echo off
REM ==========================================
REM ローカル環境セットアップスクリプト (Windows)
REM ==========================================

echo ==========================================
echo ワークフロー申請システム - ローカル環境セットアップ
echo ==========================================
echo.
REM ==========================================
REM プロキシ設定（ご自身の環境に合わせて書き換えてください）
REM ==========================================
set HTTPS_PROXY=http://proxy-lb.namc.local:8088
REM Python バージョン確認
echo [1/6] Python 3.13 バージョン確認...
py -3.13 --version
if %ERRORLEVEL% NEQ 0 (
    echo エラー: Python 3.13 がインストールされていません
    echo Python 3.13をインストールしてください
    echo ダウンロード: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK
echo.

REM 仮想環境の作成
echo [2/6] Python 3.13 仮想環境の作成...
if exist venv (
    echo 仮想環境は既に存在します
) else (
    py -3.13 -m venv venv
    echo Python 3.13 の仮想環境を作成しました
)
echo.

REM 仮想環境のアクティベート
echo [3/6] 仮想環境のアクティベート...
call venv\Scripts\activate.bat
echo OK
echo.

REM 依存パッケージのインストール
echo [4/6] 依存パッケージのインストール...
pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo エラー: パッケージのインストールに失敗しました
    pause
    exit /b 1
)
echo OK
echo.

REM .env ファイルの作成
echo [5/6] 環境変数ファイルの作成...
if exist .env (
    echo .env ファイルは既に存在します
) else (
    copy .env.example .env
    echo .env ファイルを作成しました
    echo 重要: .env ファイルを編集してデータベース接続情報を設定してください
)
echo.

REM ログディレクトリの作成
echo [6/6] ログディレクトリの作成...
if not exist logs mkdir logs
echo OK
echo.

echo ==========================================
echo セットアップが完了しました！
echo ==========================================
echo.
echo 次のステップ:
echo 1. .env ファイルを編集してデータベース接続情報を設定
echo 2. データベースにテーブルを作成（database/*.sql を実行）
echo 3. python run.py でサーバーを起動
echo.
echo 詳細は docs\local_testing_guide.md を参照してください
echo.
pause
