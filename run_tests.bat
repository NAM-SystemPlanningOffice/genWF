@echo off
REM テスト実行用バッチファイル

echo ================================
echo genWF 回帰テスト実行
echo ================================
echo.

REM 仮想環境を有効化
call venv\Scripts\activate

REM 引数に応じてテストを実行
if "%1"=="" (
    echo すべてのテストを実行します...
    pytest -v
) else if "%1"=="unit" (
    echo 単体テストを実行します...
    pytest -m unit -v
) else if "%1"=="integration" (
    echo 統合テストを実行します...
    pytest -m integration -v
) else if "%1"=="e2e" (
    echo E2Eテストを実行します...
    pytest -m e2e -v
) else if "%1"=="coverage" (
    echo カバレッジレポート付きでテストを実行します...
    pytest --cov=app --cov-report=html --cov-report=term-missing
    echo.
    echo カバレッジレポートは htmlcov\index.html で確認できます
) else if "%1"=="quick" (
    echo 単体テスト（高速）を実行します...
    pytest -m "unit and not slow" -v
) else (
    echo 使用方法:
    echo   run_tests.bat          - すべてのテストを実行
    echo   run_tests.bat unit     - 単体テストのみ
    echo   run_tests.bat integration - 統合テストのみ
    echo   run_tests.bat e2e      - E2Eテストのみ
    echo   run_tests.bat coverage - カバレッジレポート付き
    echo   run_tests.bat quick    - 高速テストのみ
)

echo.
echo ================================
echo テスト実行完了
echo ================================
pause
