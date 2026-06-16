@echo off
REM ハイブリッドDBテスト実行用バッチファイル

echo ================================
echo ハイブリッドDBテスト実行
echo ================================
echo.
echo 注意: このテストは実DBに接続します
echo - マスタテーブル（M_*）: 読み取りのみ
echo - トランザクションテーブル（T_*）: 作成・削除
echo.
echo テストデータは自動的にクリーンアップされます
echo.

REM 確認プロンプト
set /p CONFIRM="実行しますか？ (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo キャンセルしました
    pause
    exit /b
)

echo.
echo テスト実行中...
echo.

REM 仮想環境を有効化
call venv\Scripts\activate

REM ハイブリッドDBテストを実行
pytest -m hybrid_db --cov=app --cov-report=html --cov-report=term-missing -v -s

echo.
echo ================================
echo テスト実行完了
echo ================================
echo.
echo カバレッジレポート: htmlcov\index.html
echo.

REM クリーンアップ確認
echo クリーンアップ確認を実行しますか？
set /p CLEANUP="(y/N): "
if /i "%CLEANUP%"=="y" (
    echo.
    echo クリーンアップ確認中...
    pytest tests/integration/test_hybrid_db.py::TestHybridDBCleanup::test_cleanup_verification -v
)

pause
