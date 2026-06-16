# ワークフロー申請システム

システム関係の各種申請業務と承認フローを管理するWebアプリケーションです。

## 技術スタック

- **本番環境**: Azure App Service (Linux) + Gunicorn
- **開発環境**: Flask開発サーバー（ローカルPC）
- **アプリケーション**: Python 3.11 + Flask
- **認証**: Entra ID Easy Auth (本番) / 手動ログイン (開発)
- **データベース接続**: python-oracledb (Thin mode - Oracle Instant Client不要)
- **データベース**: Oracle Database (TSTCOMDB スキーマ: NAM_TASK)

## 主要機能

### 申請者向け機能
- 新規申請作成（Gmailグループ、データベースアクセス権限等）
- 既存リソースの修正・削除申請
- 申請の下書き保存
- 申請一覧・詳細確認

### 承認者向け機能
- 承認待ちタスク一覧
- 申請内容の確認・承認・却下
- 承認履歴の確認

### 管理者向け機能
- 申請種類マスタ管理
- ワークフロー定義管理
- リソース同期管理

## ディレクトリ構成

```
genWF/
├── app/                      # アプリケーション本体
│   ├── models/               # データモデル
│   ├── services/             # ビジネスロジック
│   ├── routes/               # ルーティング
│   ├── templates/            # HTMLテンプレート
│   ├── static/               # 静的ファイル
│   └── utils/                # ユーティリティ
├── database/                 # DDL・サンプルデータ
├── docs/                     # ドキュメント
├── logs/                     # ログファイル
├── scripts/                  # バッチスクリプト
├── tests/                    # テストコード
├── .env                      # 環境変数（Gitにコミットしない）
├── requirements.txt          # Python依存パッケージ
└── run.py                    # 開発サーバー起動スクリプト
```

## セットアップ手順

### 1. リポジトリのクローン

```bash
cd c:\Users\ootagaki\claude1
git clone <repository-url> genWF
cd genWF
```

### 2. Python仮想環境の作成

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. Oracle接続について（python-oracledb）

**重要**: python-oracledb（oracledb）は、デフォルトでThin modeで動作します。
**Oracle Instant Clientのインストールは不要です！**

Thin mode（デフォルト）:
- Pure Python実装
- Oracle Instant Client不要
- セットアップが簡単
- 通常の用途には十分な性能

Thick mode（オプション）:
- Oracle Instant Clientが必要
- より高速（大量データ処理時）
- `.env` で `USE_THICK_MODE=True` に設定

参考: https://python-oracledb.readthedocs.io/

### 5. データベースの作成

Oracle SQLPlusまたはSQL Developerで以下のSQLを実行してください。

```bash
# スキーマに接続
sqlplus NAM_TASK/password@ORCL

# テーブル作成
@database/01_create_tables.sql

# 外部キー作成
@database/02_create_foreign_keys.sql

# サンプルデータ投入
@database/03_insert_sample_data.sql
```

### 6. 環境変数の設定

`.env.example` を `.env` にコピーして、環境に合わせて編集してください。

```bash
copy .env.example .env
```

`.env` ファイルの内容:

```
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

ORACLE_DSN=localhost:1521/ORCL
ORACLE_USER=NAM_TASK
ORACLE_PASSWORD=your-password-here

ITEMS_PER_PAGE=20
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 7. ログディレクトリの作成

```bash
mkdir logs
```

### 8. 開発サーバーの起動

```bash
python run.py
```

ブラウザで http://localhost:5000/auth/login にアクセスしてください。
ユーザーIDを入力してログインします（手動ログイン）。

## 開発

### コードスタイル

Black（コードフォーマッター）を使用します。

```bash
black app/
```

### テスト実行

```bash
pytest tests/
```

### ログ確認

アプリケーションのログは `logs/app.log` に出力されます。

```bash
tail -f logs/app.log  # Linux/Mac
Get-Content logs/app.log -Wait  # Windows PowerShell
```

## Azure App Serviceへのデプロイ（本番環境）

本番環境では **Azure App Service (Linux) + Gunicorn + Entra ID Easy Auth** を使用します。

### セットアップ手順

詳細は [docs/APP_SERVICE_SETUP.md](docs/APP_SERVICE_SETUP.md) を参照してください。

#### 概要

1. **App Service リソースの作成**
   - Python 3.11 ランタイム
   - Staging スロットの作成

2. **環境変数の設定**
   - スロット固有設定: `DEPLOYMENT_SLOT`, `ORACLE_DSN`, `ORACLE_USER`, `ORACLE_PASSWORD`
   - 共通設定: `SECRET_KEY`, アプリ設定

3. **Entra ID Easy Auth の設定**
   - Entra ID アプリ登録
   - Easy Auth の有効化（Staging / Production 両方）

4. **デプロイ**
   - Git デプロイ / GitHub Actions / ZIP デプロイ
   - Staging スロットにデプロイ → 動作確認 → Production にスワップ

5. **動作確認**
   - Staging: `https://genWF-app-staging.azurewebsites.net/auth/login`
   - Production: `https://genWF-app.azurewebsites.net/auth/login`

## ドキュメント

### 環境構築・運用
- **[Azure App Service デプロイ手順](docs/APP_SERVICE_SETUP.md)** - Entra ID Easy Auth設定とデプロイスロット運用

### 設計書
- [システム構成要素](docs/system_architecture.md)
- [データベース設計](docs/database_design.md)
- [申請区分と機能設計](docs/application_action_types.md)
- [申請対象ユーザーと所管所属](docs/application_user_types.md)
- [承認待ちタスク設計](docs/approval_task_design.md)
- [アプリケーション構成](docs/application_structure.md)

### 自動処理機能
- **[自動処理機能（簡素化版）](docs/AUTO_PROCESS_SIMPLIFIED.md)** - 最新の簡素化設計ガイド
- **[自動処理設定例（簡素化版）](docs/AUTO_PROCESS_EXAMPLES_SIMPLIFIED.md)** - 実用的な設定例
- [自動処理設定ガイド（旧版）](docs/AUTO_PROCESS_CONFIGURATION.md) - 旧設計のガイド
- [自動処理設定例（旧版）](docs/AUTO_PROCESS_EXAMPLES.md) - 旧設計の設定例

## トラブルシューティング

### Oracle接続エラー

```
DPI-1047: Cannot locate a 64-bit Oracle Client library
```

→ Oracle Instant Client のパスが正しく設定されていません。環境変数 `PATH` を確認してください。

### インポートエラー

```
ModuleNotFoundError: No module named 'cx_Oracle'
```

→ 仮想環境がアクティブになっているか確認し、`pip install -r requirements.txt` を実行してください。

### データベース接続エラー

```
ORA-12545: Connect failed because target host or object does not exist
```

→ `.env` ファイルの `ORACLE_DSN` が正しく設定されているか確認してください。

## ライセンス

社内利用のため、ライセンスは非公開です。

## 作成者

システム企画室

## 更新履歴

- 2026-05-20: 初版作成
