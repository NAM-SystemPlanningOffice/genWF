# 実装サマリ

## 作成済みファイル一覧

### データベース関連
- `database/01_create_tables.sql` - テーブル作成DDL
- `database/02_create_foreign_keys.sql` - 外部キー制約
- `database/03_insert_sample_data.sql` - サンプルデータ

### Python アプリケーション基盤
- `run.py` - 開発サーバー起動スクリプト
- `requirements.txt` - Python依存パッケージ
- `.env.example` - 環境変数サンプル

### アプリケーション設定
- `app/__init__.py` - Flaskアプリケーションファクトリ
- `app/config.py` - 設定ファイル

### ユーティリティ
- `app/utils/__init__.py`
- `app/utils/db.py` - データベース接続管理
- `app/utils/decorators.py` - デコレーター（認証等）
- `app/utils/helpers.py` - ヘルパー関数
- `app/utils/constants.py` - 定数定義

### モデル
- `app/models/__init__.py`
- `app/models/user.py` - ユーザー情報モデル

### ドキュメント
- `README.md` - プロジェクトREADME
- `docs/system_architecture.md` - システム構成要素
- `docs/database_design.md` - データベース設計
- `docs/application_action_types.md` - 申請区分と機能設計
- `docs/application_user_types.md` - 申請対象ユーザーと所管所属設計
- `docs/approval_task_design.md` - 承認待ちタスク設計
- `docs/application_structure.md` - アプリケーション構成
- `docs/application_structure_services.md` - Services & Routes層
- `docs/application_structure_templates.md` - HTMLテンプレート構成

## 次に実装すべきファイル

### 優先度: 高

#### Models層（残り）
1. `app/models/application.py` - 申請関連モデル
   - Application クラス
   - ApplicationDetail クラス

2. `app/models/workflow.py` - ワークフロー関連モデル
   - WorkflowInstance クラス
   - WorkflowNodeInstance クラス
   - WorkflowNodeApprover クラス
   - WorkflowHistory クラス

3. `app/models/master.py` - マスタ関連モデル
   - ApplicationType クラス
   - ApplicationField クラス
   - WorkflowDefinition クラス
   - WorkflowNodeDefinition クラス
   - 等

4. `app/models/resource.py` - リソース関連モデル
   - ResourceService クラス

#### Services層
1. `app/services/__init__.py`

2. `app/services/application_service.py` - 申請処理サービス
   - create_draft()
   - update_draft()
   - submit_application()
   - get_application_form_fields()

3. `app/services/workflow_service.py` - ワークフロー処理サービス
   - start_workflow()
   - advance_to_next_node()
   - _register_approvers()
   - _get_approvers_for_node()

4. `app/services/approval_service.py` - 承認処理サービス
   - approve()
   - reject()
   - get_pending_tasks()

5. `app/services/validation_service.py` - バリデーションサービス
   - validate_application()
   - validate_field()

6. `app/services/resource_service.py` - リソース検索サービス
   - search_resources()
   - get_resource_detail()
   - validate_resource_duplication()

7. `app/services/notification_service.py` - 通知サービス
   - notify_approvers()
   - send_email()

#### Routes層
1. `app/routes/__init__.py`

2. `app/routes/auth.py` - 認証関連
   - login()
   - logout()

3. `app/routes/application.py` - 申請画面
   - index() - 申請種類選択
   - create() - 新規作成
   - modify() - 修正
   - delete() - 削除
   - search_resource() - リソース検索
   - list() - 申請一覧
   - detail() - 申請詳細

4. `app/routes/approval.py` - 承認画面
   - task_list() - 承認待ちタスク一覧
   - task_detail() - タスク詳細
   - approve() - 承認実行
   - reject() - 却下実行

5. `app/routes/admin.py` - 管理画面
   - dashboard()
   - application_type()
   - workflow_definition()

6. `app/routes/api.py` - Ajax API
   - pulldown_options()
   - validate_field()

### 優先度: 中

#### テンプレート
1. `app/templates/base.html` - ベーステンプレート
2. `app/templates/layout/header.html`
3. `app/templates/layout/sidebar.html`
4. `app/templates/layout/footer.html`
5. `app/templates/layout/breadcrumb.html`

6. `app/templates/auth/login.html`
7. `app/templates/auth/logout.html`

8. `app/templates/application/index.html` - 申請種類選択
9. `app/templates/application/create.html` - 新規申請作成
10. `app/templates/application/modify.html` - 修正申請
11. `app/templates/application/search_resource.html` - リソース検索
12. `app/templates/application/list.html` - 申請一覧
13. `app/templates/application/detail.html` - 申請詳細

14. `app/templates/approval/task_list.html` - 承認待ちタスク一覧
15. `app/templates/approval/task_detail.html` - タスク詳細・承認

16. `app/templates/errors/400.html`
17. `app/templates/errors/403.html`
18. `app/templates/errors/404.html`
19. `app/templates/errors/500.html`

#### 静的ファイル
1. `app/static/css/style.css` - メインスタイル
2. `app/static/js/main.js` - メインJavaScript
3. `app/static/js/application.js` - 申請画面用JS
4. `app/static/js/approval.js` - 承認画面用JS

### 優先度: 低

#### バッチスクリプト
1. `scripts/sync_resources.py` - リソース同期バッチ
2. `scripts/send_notifications.py` - 通知送信バッチ

#### テスト
1. `tests/test_application.py`
2. `tests/test_workflow.py`
3. `tests/test_approval.py`

## 実装の進め方

### フェーズ1: 基本機能（1-2週間）
1. Models層の完成
2. Services層の基本実装
3. 認証機能（ダミー実装でOK）
4. 申請作成機能（新規作成のみ）
5. ベーステンプレートとログイン画面

### フェーズ2: ワークフロー機能（1-2週間）
1. ワークフロー開始機能
2. 承認待ちタスク一覧
3. 承認・却下機能
4. 申請一覧・詳細画面

### フェーズ3: 高度な機能（1-2週間）
1. 修正・削除申請
2. リソース検索機能
3. バリデーション機能
4. 管理画面

### フェーズ4: 運用機能（1週間）
1. リソース同期バッチ
2. 通知機能
3. エラーハンドリング
4. ログ出力

### フェーズ5: テスト・デプロイ（1週間）
1. 単体テスト
2. 結合テスト
3. Azure App Serviceへのデプロイ設定
4. Staging環境セットアップ
5. Production環境セットアップ

## 開発時の注意点

### データベース接続
- cx_Oracle の接続プールを使用することを推奨
- トランザクション管理を適切に行う（commit/rollback）
- 接続リークに注意

### セキュリティ
- SQLインジェクション対策（プレースホルダーの使用）
- XSS対策（テンプレートの自動エスケープ）
- CSRF対策（Flask-WTF）
- セッション管理（適切なタイムアウト設定）

### パフォーマンス
- 承認待ち一覧のインデックス設計
- N+1問題の回避
- 適切なページネーション

### エラーハンドリング
- データベースエラーの適切な処理
- ユーザーフレンドリーなエラーメッセージ
- エラーログの詳細記録

### テスト
- ユニットテストの作成
- モックを使用した外部依存の排除
- テストカバレッジの確保

## デプロイチェックリスト

### 開発環境 → テスト環境
- [ ] .env ファイルの設定確認
- [ ] データベース接続確認
- [ ] サンプルデータ投入
- [ ] 基本機能の動作確認

### Staging環境 → Production環境
- [ ] SECRET_KEY の設定
- [ ] DEPLOYMENT_SLOT の確認（staging/production）
- [ ] ログレベルの変更（staging=INFO, production=WARNING）
- [ ] データベース接続情報の変更（スロット固有設定）
- [ ] Entra ID Easy Auth の設定確認
- [ ] SSL証明書の設定（App Service managed certificate）
- [ ] バックアップ設定
- [ ] 監視設定（Application Insights）

## サポート・連絡先

実装に関する質問や問題があれば、システム企画室までご連絡ください。

- メール: sys-planning@example.com
- 内線: XXXX
