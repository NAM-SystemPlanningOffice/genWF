#!/bin/bash
# テスト実行用スクリプト（Linux/Mac用）

echo "================================"
echo "genWF 回帰テスト実行"
echo "================================"
echo ""

# 仮想環境を有効化
source venv/bin/activate

# 引数に応じてテストを実行
case "$1" in
    "")
        echo "すべてのテストを実行します..."
        pytest -v
        ;;
    "unit")
        echo "単体テストを実行します..."
        pytest -m unit -v
        ;;
    "integration")
        echo "統合テストを実行します..."
        pytest -m integration -v
        ;;
    "e2e")
        echo "E2Eテストを実行します..."
        pytest -m e2e -v
        ;;
    "coverage")
        echo "カバレッジレポート付きでテストを実行します..."
        pytest --cov=app --cov-report=html --cov-report=term-missing
        echo ""
        echo "カバレッジレポートは htmlcov/index.html で確認できます"
        ;;
    "quick")
        echo "単体テスト（高速）を実行します..."
        pytest -m "unit and not slow" -v
        ;;
    *)
        echo "使用方法:"
        echo "  ./run_tests.sh          - すべてのテストを実行"
        echo "  ./run_tests.sh unit     - 単体テストのみ"
        echo "  ./run_tests.sh integration - 統合テストのみ"
        echo "  ./run_tests.sh e2e      - E2Eテストのみ"
        echo "  ./run_tests.sh coverage - カバレッジレポート付き"
        echo "  ./run_tests.sh quick    - 高速テストのみ"
        ;;
esac

echo ""
echo "================================"
echo "テスト実行完了"
echo "================================"
