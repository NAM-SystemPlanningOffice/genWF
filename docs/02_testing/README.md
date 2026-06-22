# テスト実施ガイド

開発者がテストを実施するためのドキュメント集です。

## 📚 ドキュメント一覧

### テスト全体

- [TESTING.md](TESTING.md) - テスト全体の概要と方針

### テスト戦略

- [DATABASE_TESTING.md](strategies/DATABASE_TESTING.md) - データベーステスト戦略（実DB vs モック）
- [HYBRID_DB_TESTING.md](strategies/HYBRID_DB_TESTING.md) - ハイブリッドDBテスト戦略
- [TEST_SAFETY_ANALYSIS.md](strategies/TEST_SAFETY_ANALYSIS.md) - テスト実行の安全性分析
- [VISUAL_TESTING.md](strategies/VISUAL_TESTING.md) - ビジュアルテスト（UI/画面表示テスト）
- [RESOURCE_SELECTION_TESTING.md](strategies/RESOURCE_SELECTION_TESTING.md) - リソース選択機能のテスト

### カバレッジ

- [COVERAGE_GUIDE.md](coverage/COVERAGE_GUIDE.md) - カバレッジ測定ガイド
- [COVERAGE_EXPLANATION.md](coverage/COVERAGE_EXPLANATION.md) - カバレッジの見方と解釈
- [TEST_DATA_CONFIGURATION.md](coverage/TEST_DATA_CONFIGURATION.md) - テストデータの設定方法

## 🎯 テスト実施の流れ

### 初めてテストを実行する

1. **環境構築** → [../00_infrastructure/local_setup/local_testing_guide.md](../00_infrastructure/local_setup/local_testing_guide.md)
2. **テスト全体方針を理解** → [TESTING.md](TESTING.md)
3. **テストを実行**
   ```bash
   pytest
   ```

### テスト戦略を理解する

1. **データベーステスト戦略** → [DATABASE_TESTING.md](strategies/DATABASE_TESTING.md)
2. **ハイブリッド戦略** → [HYBRID_DB_TESTING.md](strategies/HYBRID_DB_TESTING.md)
3. **安全性分析** → [TEST_SAFETY_ANALYSIS.md](strategies/TEST_SAFETY_ANALYSIS.md)

### カバレッジを測定する

1. **カバレッジ測定方法** → [COVERAGE_GUIDE.md](coverage/COVERAGE_GUIDE.md)
2. **結果の見方** → [COVERAGE_EXPLANATION.md](coverage/COVERAGE_EXPLANATION.md)

### 特定機能のテスト

- **画面表示テスト** → [VISUAL_TESTING.md](strategies/VISUAL_TESTING.md)
- **リソース選択機能** → [RESOURCE_SELECTION_TESTING.md](strategies/RESOURCE_SELECTION_TESTING.md)

## 🔗 関連ドキュメント

- 環境構築したい → [00_infrastructure/](../00_infrastructure/)
- アプリケーション構造を理解したい → [01_development/](../01_development/)
- 申請業務を登録したい → [03_administration/](../03_administration/)
