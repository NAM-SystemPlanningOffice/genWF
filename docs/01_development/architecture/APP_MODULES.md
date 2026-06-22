# アプリケーションモジュール構成ドキュメント

本ドキュメントは、`app/` ディレクトリ配下の各Pythonモジュールの役割と責務を整理したものです。

## 目次

- [ディレクトリ構成](#ディレクトリ構成)
- [コアモジュール](#コアモジュール)
- [モデル層 (models)](#モデル層-models)
- [ルート層 (routes)](#ルート層-routes)
- [サービス層 (services)](#サービス層-services)
- [ユーティリティ層 (utils)](#ユーティリティ層-utils)

---

## ディレクトリ構成

```
app/
├── __init__.py              # Flaskアプリケーション初期化
├── config.py                # アプリケーション設定
├── models/                  # データモデル層
│   ├── admin/              # 管理画面用モデル
│   └── *.py                # 各種モデル
├── routes/                  # ルーティング層（コントローラー）
│   └── *.py                # 各種ルート
├── services/                # ビジネスロジック層
│   └── *.py                # 各種サービス
└── utils/                   # ユーティリティ層
    └── *.py                # 共通機能
```

---

## コアモジュール

### `app/__init__.py`
- **役割**: Flaskアプリケーションのファクトリ関数を提供
- **主な機能**:
  - Flaskアプリケーションインスタンスの作成
  - 各種Blueprintの登録
  - データベース接続の初期化
  - ログ設定

### `app/config.py`
- **役割**: アプリケーション全体の設定を管理
- **主な機能**:
  - データベース接続情報
  - セッション設定
  - 環境別設定（開発/本番）

---

## モデル層 (models)

データベースアクセスとデータ構造を定義するモデル群。各モデルは対応するテーブルのCRUD操作を提供します。

### `models/__init__.py`
- モデル層の初期化ファイル

### 申請関連モデル

#### `models/application.py`
- **テーブル**: `T_APPLICATION`
- **役割**: 申請の基本情報を管理
- **主な機能**:
  - 申請の作成・更新・削除
  - 申請ステータスの管理（draft, submitted, approved, rejected, returned, withdrawn）
  - 申請者・所属情報の取得

#### `models/application_detail.py`
- **テーブル**: `T_APPLICATION_DETAIL`
- **役割**: 申請の詳細情報（フィールド値）を管理
- **主な機能**:
  - 申請フィールド値の保存・取得
  - 複数レコード申請のサポート（detail_seq）
  - 修正・追加・削除アクション（detail_action）の管理

#### `models/application_type.py`
- **テーブル**: `M_APPLICATION_TYPE`
- **役割**: 申請種類のマスタ情報を管理
- **主な機能**:
  - 申請種類の一覧取得（アクティブ、開発中含む）
  - 申請可能制限のチェック（所属・ユーザーIDベース）
  - リソース検索クエリの管理
  - ワークフロー定義との紐付け

#### `models/application_field.py`
- **テーブル**: `M_APPLICATION_FIELD`
- **役割**: 申請フィールド定義を管理
- **主な機能**:
  - 申請種類ごとのフィールド一覧取得
  - プルダウン選択肢の取得（静的・動的）
  - フィールドタイプ（text, select, date等）の管理
  - 表示順・必須・可視性の制御

### ワークフロー関連モデル

#### `models/workflow.py`
- **テーブル**: `M_WORKFLOW_DEFINITION`, `T_WORKFLOW_INSTANCE`, `T_WORKFLOW_NODE_INSTANCE`
- **役割**: ワークフロー定義とインスタンスを管理
- **主なクラス**:
  - `WorkflowDefinition`: ワークフロー定義マスタ
  - `WorkflowInstance`: ワークフローインスタンス（申請ごと）
  - `WorkflowNodeInstance`: ノードインスタンス（承認ステップごと）
- **主な機能**:
  - ワークフローの開始・進行・完了
  - ノードステータスの管理（waiting, pending, approved, rejected, returned, skipped, withdrawn）
  - 現在ノードの追跡

#### `models/approval_task.py`
- **テーブル**: `T_WORKFLOW_NODE_APPROVER`
- **役割**: 承認タスク（承認者と承認状態）を管理
- **主な機能**:
  - 承認者の登録・取得
  - 承認ステータスの管理（pending, approved, rejected, returned, completed_by_peer）
  - 通知フラグ（is_notified）の管理
  - グループ承認（approver_group）のサポート

### ユーザー・リソース関連モデル

#### `models/user.py`
- **テーブル**: `nam_user_admin.e_imdb2_users`, `nam_user_admin.e_approver`
- **役割**: ユーザー情報と承認者情報を管理
- **主な機能**:
  - ユーザー情報の取得
  - ユーザーの所属一覧取得（本務・兼務）
  - 所属別承認者の取得
  - リソース・所属ベースの承認者取得

#### `models/admin_user.py`
- **テーブル**: `M_ADMIN_USER`
- **役割**: システム管理者を管理
- **主な機能**:
  - 管理者権限のチェック
  - 管理者の登録・削除

#### `models/resource.py`
- **テーブル**: 動的（申請種類ごとに異なるビュー）
- **役割**: 申請対象リソースの検索・取得
- **主な機能**:
  - リソース検索（動的クエリ実行）
  - リソース詳細取得
  - 所管所属情報の取得

### 管理画面用モデル (models/admin/)

#### `models/admin/application_type.py`
- **テーブル**: `M_APPLICATION_TYPE`
- **役割**: 申請種類マスタの管理画面用CRUD操作
- **主な機能**:
  - 申請種類の作成・更新・削除
  - 開発中フラグの管理
  - ワークフロー定義との紐付け

#### `models/admin/application_field.py`
- **テーブル**: `M_APPLICATION_FIELD`
- **役割**: 申請フィールドマスタの管理画面用CRUD操作
- **主な機能**:
  - フィールドの作成・更新・削除
  - 表示順の管理
  - プルダウングループとの紐付け

#### `models/admin/pulldown_group.py`
- **テーブル**: `M_PULLDOWN_GROUP`
- **役割**: プルダウングループマスタを管理
- **主な機能**:
  - プルダウングループの作成・更新・削除
  - 静的・動的プルダウンの切り替え
  - 動的クエリの管理

#### `models/admin/pulldown_option.py`
- **テーブル**: `M_PULLDOWN_OPTION`
- **役割**: 静的プルダウン選択肢を管理
- **主な機能**:
  - 選択肢の作成・更新・削除
  - 表示順の管理

#### `models/admin/validation_rule.py`
- **テーブル**: `M_VALIDATION_RULE`
- **役割**: バリデーションルールマスタを管理
- **主な機能**:
  - ルールの作成・更新・削除
  - ルールタイプ（required, unique, regex, query等）の管理
  - エラーメッセージのカスタマイズ

#### `models/admin/field_validation.py`
- **テーブル**: `M_FIELD_VALIDATION`
- **役割**: フィールドとバリデーションルールの紐付けを管理
- **主な機能**:
  - フィールドへのルール適用・解除
  - 作成時・修正時の適用条件管理

#### `models/admin/workflow_definition.py`
- **テーブル**: `M_WORKFLOW_DEFINITION`
- **役割**: ワークフロー定義マスタの管理画面用CRUD操作
- **主な機能**:
  - ワークフロー定義の作成・更新・削除
  - バージョン管理

#### `models/admin/workflow_node_definition.py`
- **テーブル**: `M_WORKFLOW_NODE_DEFINITION`
- **役割**: ワークフローノード定義マスタの管理画面用CRUD操作
- **主な機能**:
  - ノード定義の作成・更新・削除
  - ノードタイプ（applicant_dept, jurisdiction_dept, specific_node等）の管理
  - スキップ条件の設定
  - 承認者選択要否の管理

#### `models/admin/audit_log.py`
- **テーブル**: `T_AUDIT_LOG`
- **役割**: 監査ログの記録と取得
- **主な機能**:
  - 管理画面での操作ログ記録
  - ログの検索・一覧表示

---

## ルート層 (routes)

HTTPリクエストを処理し、モデル・サービスを呼び出してレスポンスを返すコントローラー層。

### `routes/__init__.py`
- ルート層の初期化ファイル

### `routes/auth.py`
- **URL Prefix**: `/auth`
- **役割**: 認証・ログイン・ログアウト処理
- **主なエンドポイント**:
  - `GET/POST /login`: ログイン画面（SSO対応）
  - `GET/POST /select-department`: 所属選択画面
  - `GET /logout`: ログアウト
- **特記事項**:
  - staging/production環境: Entra ID Easy Auth（SSO）
  - 開発環境: フォームログイン
  - 所属が1つの場合は自動選択してスキップ

### `routes/application.py`
- **URL Prefix**: `/application`
- **役割**: 申請の作成・閲覧・編集・取り下げ処理
- **主なエンドポイント**:
  - `GET /`: 申請種類選択画面
  - `GET /create/<application_type_id>`: 新規申請作成画面
  - `POST /create/<application_type_id>/submit`: 新規申請提出
  - `GET /modify/<application_type_id>`: 修正申請（リソース検索）
  - `GET /delete/<application_type_id>`: 削除申請（リソース検索）
  - `GET /detail/<application_id>`: 申請詳細画面
  - `GET /edit/<application_id>`: 下書き編集画面
  - `POST /edit/<application_id>/submit`: 下書き更新・提出
  - `GET /select-approvers/<application_id>`: 承認者選択画面
  - `POST /confirm-approvers`: 承認者確定・ワークフロー開始
  - `POST /withdraw/<application_id>`: 申請取り下げ
  - `GET /list`: 統合タスク一覧（申請一覧 + 承認タスク）
  - `POST /recall-node/<node_instance_id>`: 承認引き戻し
- **特記事項**:
  - 承認者が複数いる場合は`is_notified`選択画面を表示
  - 取り下げは最初のノードがpendingの場合のみ可能

### `routes/application_modify.py`
- **URL Prefix**: `/application`
- **役割**: 修正・削除申請の提出処理
- **主なエンドポイント**:
  - `POST /modify/<application_type_id>/<resource_id>/submit`: 修正申請提出
- **特記事項**:
  - リソースIDを指定した申請
  - 所管所属の自動取得
  - 実施予定日のサポート

### `routes/application_multi.py`
- **URL Prefix**: `/application`
- **役割**: 複数レコード申請の作成・編集処理
- **主なエンドポイント**:
  - `GET /multi/<application_type_id>`: 複数レコード申請作成画面
  - `POST /multi/<application_type_id>/<resource_id>/submit`: 複数レコード申請提出
  - `GET /edit-multi/<application_id>`: 複数レコード申請編集画面
  - `POST /edit-multi/<application_id>/<application_type_id>/<resource_id>/submit`: 複数レコード申請更新・提出
- **特記事項**:
  - 複数レコードの一括入力
  - 各レコードに対するアクション（add, modify, delete）の指定

### `routes/approval.py`
- **URL Prefix**: `/approval`
- **役割**: 承認・却下・差し戻し処理
- **主なエンドポイント**:
  - `GET /task/<node_instance_id>`: 承認タスク詳細画面
  - `POST /approve/<node_instance_id>`: 承認
  - `POST /reject/<node_instance_id>`: 却下
  - `POST /return/<node_instance_id>`: 差し戻し
- **特記事項**:
  - コメント入力必須（却下・差し戻し）
  - グループ承認対応（複数所属長承認）

### `routes/admin.py`
- **URL Prefix**: `/admin`
- **役割**: 管理画面（マスタ管理）
- **主なエンドポイント**:
  - 申請種類管理（CRUD）
  - 申請フィールド管理（CRUD）
  - プルダウングループ・選択肢管理（CRUD）
  - バリデーションルール管理（CRUD）
  - ワークフロー定義管理（CRUD）
  - ワークフローノード定義管理（CRUD）
  - 管理者ユーザー管理（追加・削除）
  - 監査ログ閲覧
- **特記事項**:
  - `@login_required` + `@admin_required` による管理者権限チェック

### `routes/api.py`
- **URL Prefix**: `/api`
- **役割**: REST API（動的プルダウン取得等）
- **主なエンドポイント**:
  - `GET /pulldown-options/<pulldown_group_id>`: プルダウン選択肢取得（動的）
- **特記事項**:
  - JSON形式でレスポンス
  - バインド変数をクエリパラメータで受け取る

---

## サービス層 (services)

ビジネスロジックを集約し、複数のモデルにまたがる複雑な処理を実装するレイヤー。

### `services/__init__.py`
- サービス層の初期化ファイル

### `services/workflow_service.py`
- **役割**: ワークフローの開始・進行・完了を管理
- **主なメソッド**:
  - `start_workflow(application_id, selected_approvers)`: ワークフロー開始
    - ノードインスタンス作成
    - 承認者の決定と登録
    - スキップ条件の評価
    - 最初のノードをpendingに設定
  - `approve_node(node_instance_id, approver_user_id, comment)`: ノード承認
    - 承認者のステータス更新
    - 他の承認者を`completed_by_peer`に更新（通常ノード・グループノード対応）
    - 全承認者承認済みかチェック
    - 次のノードへ進行
  - `reject_node(node_instance_id, approver_user_id, comment)`: ノード却下
  - `return_node(node_instance_id, approver_user_id, comment)`: ノード差し戻し
  - `recall_node(node_instance_id, user_id)`: 承認引き戻し
    - 自分のノードをpendingに戻す
    - 他の承認者を`pending`に戻す（通常ノード・グループノード対応）
    - 次のノード以降をwaitingに戻す
- **特記事項**:
  - 承認者決定ロジック（所属長、特定ノード、特定部署、リソース所管、複数所属長）
  - スキップ条件の動的評価（Pythonの`eval`を使用）
  - グループ承認と通常承認の統一的な処理

### `services/validation_service.py`
- **役割**: 申請フィールドのバリデーション実行
- **主なメソッド**:
  - `validate_field(field_id, value, operation_type, resource_id)`: フィールドバリデーション
    - 必須チェック（required）
    - ユニークチェック（unique, unique_per_resource）
    - 正規表現チェック（regex）
    - クエリベースチェック（query）
    - カスタムバリデーション（custom）
- **特記事項**:
  - 作成時・修正時で適用するルールを切り替え
  - エラーメッセージのカスタマイズ対応

---

## ユーティリティ層 (utils)

アプリケーション全体で使用する共通機能を提供するレイヤー。

### `utils/__init__.py`
- ユーティリティ層の初期化ファイル

### `utils/db.py`
- **役割**: データベース接続と共通処理
- **主な機能**:
  - `get_db_connection()`: Oracle DB接続取得（cx_Oracle）
  - `dict_factory(cursor)`: カーソル結果を辞書形式に変換
  - `dict_fetchone(cursor)`: 1行取得（辞書形式）
  - `dict_fetchall(cursor)`: 全行取得（辞書形式）
- **特記事項**:
  - 環境変数からDB接続情報を取得
  - カラム名を小文字に変換

### `utils/db_mock.py`
- **役割**: モックデータベース（開発・テスト用）
- **主な機能**:
  - `get_db_connection()`: メモリ内SQLite接続を返す
  - テストデータの自動投入
- **特記事項**:
  - `USE_MOCK_DB=True` の場合に`db.py`の代わりに使用
  - 現在は未使用（将来的なテスト用途）

### `utils/decorators.py`
- **役割**: カスタムデコレータの定義
- **主な機能**:
  - `@login_required`: ログイン必須チェック
  - `@admin_required`: 管理者権限チェック
- **特記事項**:
  - セッション情報を元に認証・認可をチェック

### `utils/auth.py`
- **役割**: 認証処理（環境別）
- **主な機能**:
  - `get_authenticated_user_from_request(request)`: HTTPヘッダーからユーザーID取得
- **特記事項**:
  - staging/production: Entra ID Easy Authの`X-MS-CLIENT-PRINCIPAL-NAME`ヘッダーをパース
  - 開発環境: フォーム入力（auth.pyで処理）
  - ドメイン名（@以降）を除去してユーザーIDを取得

### `utils/constants.py`
- **役割**: アプリケーション全体で使用する定数定義
- **主な定数**:
  - アクションタイプ: `ACTION_TYPE_CREATE`, `ACTION_TYPE_MODIFY`, `ACTION_TYPE_DELETE`
  - ノードタイプ: `NODE_TYPE_APPLICANT_DEPT`, `NODE_TYPE_JURISDICTION_DEPT`, `NODE_TYPE_SPECIFIC_NODE`, 等
  - ノードステータス: `NODE_STATUS_PENDING`, `NODE_STATUS_WAITING`, 等

### `utils/helpers.py`
- **役割**: 汎用的なヘルパー関数
- **主な機能**:
  - 日付フォーマット変換
  - 文字列処理
  - その他ユーティリティ関数
- **特記事項**:
  - 現在は最小限の実装

---

## アーキテクチャ上の特徴

### レイヤー分離
- **ルート層**: HTTPリクエスト処理、バリデーション、レスポンス生成
- **サービス層**: 複雑なビジネスロジック、トランザクション管理
- **モデル層**: データアクセス、単純なCRUD操作
- **ユーティリティ層**: 共通機能

### モデルの分類
- **通常モデル**: アプリケーションで使用する読み取り・書き込み
- **管理用モデル (`admin/`)**: 管理画面専用、マスタデータのCRUD

### 命名規則
- **モデル**: テーブル名に対応（例: `Application` → `T_APPLICATION`）
- **ルート**: 機能別にファイル分割（例: `application.py`, `approval.py`）
- **サービス**: ビジネスドメイン別（例: `workflow_service.py`）

### 環境対応
- **認証**: SSO（本番）とフォームログイン（開発）の切り替え
- **データベース**: Oracle DB（本番）とモックDB（開発/テスト）の切り替え

---

## 関連ドキュメント

- [データベース設計](database_design.md)
- [ワークフロー仕様](WORKFLOW_NODE_TYPES.md)
- [Azure App Serviceセットアップ](APP_SERVICE_SETUP.md)

---

**更新日**: 2026-06-09
