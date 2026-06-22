# インフラ・環境構築ガイド

システムインフラと開発環境のセットアップに関するドキュメント集です。

## 📚 リファレンス（優先参照）

技術仕様や環境構成の**単一情報源（Single Source of Truth）**。まずここを確認してください。

- **[reference/TECH_SPECS.md](reference/TECH_SPECS.md)** - 技術仕様（Python, Flask, DB, ライブラリ）
- **[reference/ENVIRONMENTS.md](reference/ENVIRONMENTS.md)** - 環境別構成（開発/Staging/Production）
- **[reference/DIRECTORY_STRUCTURE.md](reference/DIRECTORY_STRUCTURE.md)** - ディレクトリ構成

---

## 📚 ドキュメント一覧

### システム全体

- [system_architecture.md](system_architecture.md) - システムアーキテクチャ全体像

### 稼働環境

- [APP_SERVICE_SETUP.md](environments/APP_SERVICE_SETUP.md) - Azure App Service環境構築手順（Staging/Production）

### ローカル開発環境

- [python_installation.md](local_setup/python_installation.md) - Python環境のセットアップ
- [local_testing_guide.md](local_setup/local_testing_guide.md) - ローカル開発環境のセットアップとテスト実行

## 🚀 セットアップの流れ

### 初回セットアップ（開発者）

1. **Python環境構築** → [python_installation.md](local_setup/python_installation.md)
2. **ローカル環境でのテスト実行** → [local_testing_guide.md](local_setup/local_testing_guide.md)

### Azure環境構築（インフラ管理者）

1. **システムアーキテクチャ理解** → [system_architecture.md](system_architecture.md)
2. **App Service環境構築** → [APP_SERVICE_SETUP.md](environments/APP_SERVICE_SETUP.md)

## 🔗 関連ドキュメント

- アプリケーション構造を理解したい → [01_development/](../01_development/)
- テストを実施したい → [02_testing/](../02_testing/)
- 申請業務を登録したい → [03_administration/](../03_administration/)
