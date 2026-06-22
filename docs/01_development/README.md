# 開発者ガイド - アプリケーション構成

アプリケーションのコード構造・設計を理解するためのドキュメント集です。

## 📚 ドキュメント一覧

### アーキテクチャ

- [application_structure.md](architecture/application_structure.md) - アプリケーション構造（routes/controllers層）
- [application_structure_services.md](architecture/application_structure_services.md) - サービス層の構造
- [application_structure_templates.md](architecture/application_structure_templates.md) - テンプレート層の構造とJinja2の使い方
- [APP_MODULES.md](architecture/APP_MODULES.md) - モジュール構成とディレクトリ構造
- [database_design.md](architecture/database_design.md) - データベース設計とテーブル構造

### 設計思想

- [application_user_types.md](design/application_user_types.md) - ユーザータイプの設計と役割
- [application_action_types.md](design/application_action_types.md) - アクション種別（新規/修正/削除等）の設計
- [approval_task_design.md](design/approval_task_design.md) - 承認タスクとワークフローの設計思想

### 実装

- [implementation_summary.md](implementation/implementation_summary.md) - 実装サマリーと主要機能の概要

## 🎯 読む順序（推奨）

### 初めての開発者

1. **システム全体像** → [../00_infrastructure/system_architecture.md](../00_infrastructure/system_architecture.md)
2. **モジュール構成** → [APP_MODULES.md](architecture/APP_MODULES.md)
3. **アプリケーション構造（3層）**
   - Routes/Controllers層 → [application_structure.md](architecture/application_structure.md)
   - Service層 → [application_structure_services.md](architecture/application_structure_services.md)
   - Template層 → [application_structure_templates.md](architecture/application_structure_templates.md)
4. **データベース設計** → [database_design.md](architecture/database_design.md)

### 機能追加・修正する開発者

1. **設計思想を理解**
   - [application_user_types.md](design/application_user_types.md)
   - [application_action_types.md](design/application_action_types.md)
   - [approval_task_design.md](design/approval_task_design.md)
2. **該当する層のドキュメントを参照**
   - 画面修正 → Template層
   - ビジネスロジック → Service層
   - エンドポイント追加 → Routes/Controllers層

## 🔗 関連ドキュメント

- 環境構築したい → [00_infrastructure/](../00_infrastructure/)
- テストを実施したい → [02_testing/](../02_testing/)
- 申請業務を登録したい → [03_administration/](../03_administration/)
