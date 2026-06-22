# ドキュメント目次

ワークフロー管理システムの包括的なドキュメント集です。

---

## 📚 リファレンス（技術仕様・環境構成）

**対象者**: すべての開発者・管理者

技術仕様や環境構成の**単一情報源（Single Source of Truth）**です。バージョン変更時はこれらのファイルのみ更新してください。

- **[TECH_SPECS.md](00_infrastructure/reference/TECH_SPECS.md)** - 技術仕様（Python, Flask, DB, ライブラリ）
- **[ENVIRONMENTS.md](00_infrastructure/reference/ENVIRONMENTS.md)** - 環境別構成（開発/Staging/Production）
- **[DIRECTORY_STRUCTURE.md](00_infrastructure/reference/DIRECTORY_STRUCTURE.md)** - ディレクトリ構成

---

## 📖 カテゴリ別ドキュメント

### [00_infrastructure/](00_infrastructure/) - インフラ・環境構築

システムインフラと開発環境のセットアップに関するドキュメント。

**対象者**: インフラ管理者、初めて開発環境をセットアップする開発者

- システムアーキテクチャ全体像
- Azure App Service環境構築
- ローカル開発環境セットアップ（Python、Oracle DB接続）

📘 [インフラガイドを見る →](00_infrastructure/)

---

### [01_development/](01_development/) - 開発者ガイド

アプリケーションのコード構造・設計を理解するためのドキュメント。

**対象者**: アプリケーション開発者、コードレビュアー

- アプリケーション構造（Routes/Service/Template層）
- モジュール構成とディレクトリ構造
- データベース設計
- 設計思想（ユーザータイプ、アクション種別、承認タスク）

📘 [開発者ガイドを見る →](01_development/)

---

### [02_testing/](02_testing/) - テスト実施ガイド

開発者がテストを実施するためのドキュメント。

**対象者**: テスト実施者、QA担当者、開発者

- テスト全体方針
- データベーステスト戦略（実DB vs モック、ハイブリッド戦略）
- カバレッジ測定と解釈
- ビジュアルテスト、リソース選択テスト

📘 [テストガイドを見る →](02_testing/)

---

### [03_administration/](03_administration/) - 管理者ガイド

管理者が申請業務やワークフローを登録・設定するためのドキュメント。

**対象者**: 業務管理者、システム管理者

- ワークフローセットアップガイド（ノードタイプ、スキップ条件）
- 申請フィールド設定（フィールドタイプ、複数レコードモード）
- バリデーション設定（単項目、項目間）
- JSON一括登録仕様

📘 [管理者ガイドを見る →](03_administration/)

---

## 🎯 役割別クイックスタート

### 初めて開発環境をセットアップする開発者

1. [00_infrastructure/local_setup/python_installation.md](00_infrastructure/local_setup/python_installation.md) - Python環境構築
2. [00_infrastructure/local_setup/local_testing_guide.md](00_infrastructure/local_setup/local_testing_guide.md) - ローカル環境でテスト実行
3. [01_development/architecture/APP_MODULES.md](01_development/architecture/APP_MODULES.md) - モジュール構成を理解

### コードを修正・機能追加する開発者

1. [01_development/](01_development/) - アプリケーション構造を理解
2. [02_testing/TESTING.md](02_testing/TESTING.md) - テスト方針を確認
3. 該当する層のドキュメントを参照して実装

### テストを実施する開発者

1. [02_testing/TESTING.md](02_testing/TESTING.md) - テスト全体概要
2. [02_testing/strategies/](02_testing/strategies/) - テスト戦略を選択
3. [02_testing/coverage/COVERAGE_GUIDE.md](02_testing/coverage/COVERAGE_GUIDE.md) - カバレッジ測定

### 新しい申請業務を追加する管理者

1. [03_administration/workflow_setup/WORKFLOW_SETUP_GUIDE.md](03_administration/workflow_setup/WORKFLOW_SETUP_GUIDE.md) - ワークフロー設計
2. [03_administration/application_fields/APPLICATION_TYPE_FIELDS.md](03_administration/application_fields/APPLICATION_TYPE_FIELDS.md) - フィールド設計
3. [03_administration/validation/VALIDATION_RULES.md](03_administration/validation/VALIDATION_RULES.md) - バリデーション設定

### Azure環境を構築するインフラ管理者

1. [00_infrastructure/system_architecture.md](00_infrastructure/system_architecture.md) - システムアーキテクチャ理解
2. [00_infrastructure/environments/APP_SERVICE_SETUP.md](00_infrastructure/environments/APP_SERVICE_SETUP.md) - App Service環境構築

---

## 📝 ドキュメント作成・更新のガイドライン

- 新しい機能を追加した場合は該当するカテゴリのREADME.mdにリンクを追加
- スクリーンショットは各ドキュメントと同じディレクトリに配置
- 環境構築手順は `00_infrastructure/` に配置
- アプリケーションコードの設計・構造は `01_development/` に配置
- テスト関連は `02_testing/` に配置
- 業務設定・登録手順は `03_administration/` に配置

---

**更新日**: 2026-06-17
