# ディレクトリ構成

本ドキュメントは、GenWFワークフローシステムのディレクトリ構成の**単一情報源（Single Source of Truth）**です。

---

## プロジェクト全体構成

```
genWF/
├── app/                          # アプリケーション本体
│   ├── models/                   # データモデル（DB操作）
│   ├── services/                 # ビジネスロジック
│   ├── routes/                   # ルーティング（コントローラー）
│   ├── templates/                # HTMLテンプレート（Jinja2）
│   ├── static/                   # 静的ファイル（CSS/JS/画像）
│   ├── utils/                    # ユーティリティ
│   ├── __init__.py               # Flaskアプリケーションファクトリ
│   └── config.py                 # 設定ファイル
│
├── database/                     # データベース関連
│   ├── 01_create_tables.sql      # DDL（テーブル定義）
│   └── ...                       # その他SQLスクリプト
│
├── docs/                         # ドキュメント
│   ├── 00_infrastructure/        # インフラ・環境構築
│   ├── 01_development/           # 開発者ガイド
│   ├── 02_testing/               # テストガイド
│   ├── 03_administration/        # 管理者ガイド
│   └── README.md                 # ドキュメント目次
│
├── logs/                         # ログファイル（Gitにコミットしない）
│
├── scripts/                      # バッチスクリプト
│
├── tests/                        # テストコード
│   ├── conftest.py               # pytestフィクスチャ
│   ├── test_*.py                 # 各種テスト
│   └── ...
│
├── venv/                         # Python仮想環境（Gitにコミットしない）
│
├── .env                          # 環境変数（Gitにコミットしない）
├── .gitignore                    # Git除外設定
├── CLAUDE.md                     # Claude Code用プロジェクト説明
├── README.md                     # プロジェクトREADME
├── requirements.txt              # Python依存パッケージ
├── run.py                        # 開発サーバー起動スクリプト
└── startup.sh                    # Azure App Service起動スクリプト
```

---

## app/ - アプリケーション本体

### models/ - データモデル

データベースアクセス層。テーブルごとにモデルクラスを定義。

```
app/models/
├── __init__.py
├── application.py       # 申請データモデル
├── workflow.py          # ワークフロー・タスクモデル
├── master.py            # マスタデータモデル
├── resource.py          # リソーステーブルモデル
└── user.py              # ユーザー情報モデル
```

### services/ - ビジネスロジック

ビジネスロジック層。申請処理、承認処理、バリデーション等。

```
app/services/
├── __init__.py
├── application_service.py    # 申請処理サービス
├── workflow_service.py       # ワークフロー処理サービス
├── approval_service.py       # 承認処理サービス
├── validation_service.py     # バリデーションサービス
├── resource_service.py       # リソース検索サービス
└── notification_service.py   # 通知サービス
```

### routes/ - ルーティング

コントローラー層。HTTPリクエストを受け取り、サービスを呼び出す。

```
app/routes/
├── __init__.py
├── auth.py              # 認証関連ルート
├── application.py       # 申請画面ルート
├── approval.py          # 承認画面ルート
├── admin.py             # 管理画面ルート
└── api.py               # API（Ajax用）
```

### templates/ - HTMLテンプレート

Jinja2テンプレートファイル。画面別にディレクトリ分割。

```
app/templates/
├── base.html            # ベーステンプレート
├── layout/              # レイアウト部品
│   ├── header.html
│   ├── footer.html
│   ├── sidebar.html
│   └── breadcrumb.html
│
├── auth/                # 認証画面
│   ├── login.html
│   └── logout.html
│
├── application/         # 申請画面
│   ├── index.html       # 申請種類選択
│   ├── create.html      # 新規申請作成
│   ├── modify.html      # 修正申請
│   ├── delete.html      # 削除申請
│   ├── list.html        # 申請一覧
│   └── detail.html      # 申請詳細
│
├── approval/            # 承認画面
│   ├── task_list.html   # 承認待ちタスク一覧
│   └── task_detail.html # タスク詳細・承認
│
├── admin/               # 管理画面
│   ├── dashboard.html
│   ├── application_type_list.html
│   ├── workflow_node_edit.html
│   └── ...
│
├── components/          # 再利用可能コンポーネント
│   ├── form_field.html
│   ├── table.html
│   └── pagination.html
│
└── errors/              # エラー画面
    ├── 400.html
    ├── 403.html
    ├── 404.html
    └── 500.html
```

詳細: [application_structure_templates.md](../../01_development/architecture/application_structure_templates.md)

### static/ - 静的ファイル

CSS、JavaScript、画像等の静的リソース。

```
app/static/
├── css/
│   ├── style.css        # メインスタイル
│   └── admin.css        # 管理画面用スタイル
├── js/
│   ├── main.js          # メインJavaScript
│   ├── application.js   # 申請画面用JS
│   ├── approval.js      # 承認画面用JS
│   └── admin.js         # 管理画面用JS
└── images/
    └── ...
```

### utils/ - ユーティリティ

共通ユーティリティ関数・クラス。

```
app/utils/
├── __init__.py
├── db.py                # DB接続管理
├── helpers.py           # ヘルパー関数
├── constants.py         # 定数定義
└── validators.py        # バリデーター
```

---

## docs/ - ドキュメント

ドキュメントは役割別に4つのカテゴリに分類。

```
docs/
├── 00_infrastructure/        # インフラ・環境構築
│   ├── reference/            # リファレンス（技術仕様・環境別構成）
│   ├── environments/         # 環境構築手順
│   ├── local_setup/          # ローカル開発環境セットアップ
│   ├── system_architecture.md
│   └── README.md
│
├── 01_development/           # 開発者ガイド
│   ├── architecture/         # アプリケーション構造
│   ├── design/               # 設計思想
│   ├── implementation/       # 実装詳細
│   └── README.md
│
├── 02_testing/               # テストガイド
│   ├── strategies/           # テスト戦略
│   ├── coverage/             # カバレッジ測定
│   ├── TESTING.md
│   └── README.md
│
├── 03_administration/        # 管理者ガイド
│   ├── workflow_setup/       # ワークフロー設定
│   ├── application_fields/   # 申請フィールド設定
│   ├── validation/           # バリデーション設定
│   └── README.md
│
└── README.md                 # ドキュメント目次
```

詳細: [docs/README.md](../../README.md)

---

## database/ - データベース関連

DDL、サンプルデータ等のSQLスクリプト。

```
database/
├── 01_create_tables.sql      # テーブル定義
├── 02_sample_data.sql        # サンプルデータ（開発用）
└── ...
```

---

## tests/ - テストコード

pytest形式のテストコード。

```
tests/
├── conftest.py               # フィクスチャ定義
├── test_models.py            # モデルのテスト
├── test_services.py          # サービスのテスト
├── test_routes.py            # ルーティングのテスト
├── test_validation.py        # バリデーションのテスト
└── ...
```

詳細: [02_testing/TESTING.md](../../02_testing/TESTING.md)

---

## Gitにコミットしないファイル

以下は `.gitignore` に含まれており、Gitにコミットされません：

- `venv/` - Python仮想環境
- `.env` - 環境変数（機密情報）
- `logs/` - ログファイル
- `__pycache__/` - Pythonキャッシュ
- `*.pyc` - コンパイル済みPythonファイル

---

## 関連ドキュメント

- [アプリケーション構造（Routes層）](../../01_development/architecture/application_structure.md)
- [アプリケーション構造（Service層）](../../01_development/architecture/application_structure_services.md)
- [アプリケーション構造（Template層）](../../01_development/architecture/application_structure_templates.md)
- [モジュール構成](../../01_development/architecture/APP_MODULES.md)

---

**更新日**: 2026-06-17
