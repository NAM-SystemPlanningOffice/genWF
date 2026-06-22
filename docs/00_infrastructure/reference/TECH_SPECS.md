# 技術仕様

本ドキュメントは、GenWFワークフローシステムの技術仕様の**単一情報源（Single Source of Truth）**です。

バージョン変更時は、このファイルのみ更新してください。

---

## プログラミング言語・フレームワーク

### Python

- **バージョン**: 3.13
- **選定理由**:
  - python-oracledb 最新機能のサポート
  - 型ヒントの改善（PEP 692等）
  - パフォーマンス向上
- **インストール手順**: [python_installation.md](../local_setup/python_installation.md)

### Flask

- **バージョン**: 3.x系
- **用途**: Webアプリケーションフレームワーク
- **開発環境**: Flask開発サーバー（自動リロード有効）
- **本番環境**: Gunicorn WSGIサーバー経由で実行

### Gunicorn

- **バージョン**: 最新安定版
- **用途**: 本番環境WSGIサーバー
- **環境**: Azure App Service (Staging/Production)のみ

---

## データベース

### Oracle Database

- **データベース**: COMDB (全環境共通)
- **スキーマ**: NAM_TASK (全環境共通)
- **接続先**:
  - 開発/Staging環境: ホスト `com-dbdv`
  - Production環境: ホスト `com-db`
  - ポート: `1521` (全環境共通)
- **用途**: 
  - 申請データ管理
  - ワークフロー定義管理
  - マスタデータ管理

環境別の接続設定は [ENVIRONMENTS.md](ENVIRONMENTS.md) を参照してください。

### 接続ライブラリ

- **ライブラリ**: python-oracledb
- **バージョン**: 2.x系
- **動作モード**: Thin mode（Oracle Instant Client不要）
- **インストール**: `pip install oracledb`

---

## 主要依存ライブラリ

以下は `requirements.txt` からの主要な依存関係です。

| ライブラリ | 用途 |
|-----------|------|
| Flask | Webフレームワーク |
| oracledb | Oracle Database接続 |
| Flask-Session | サーバーサイドセッション管理 |
| gunicorn | 本番環境WSGIサーバー |
| python-dotenv | 環境変数管理 |

完全なリストは [`requirements.txt`](../../../requirements.txt) を参照してください。

---

## 認証

### 開発環境

- **方式**: 手動ログイン（フォーム入力）
- **認証フロー**: ユーザーIDを入力してログイン
- **HTTPヘッダー**: なし

### Staging/Production環境

- **方式**: Entra ID Easy Auth（Azure App Service認証）
- **SSO**: Microsoft Entra IDによるシングルサインオン
- **HTTPヘッダー**: `X-MS-CLIENT-PRINCIPAL-NAME`
- **セットアップ手順**: [APP_SERVICE_SETUP.md](../environments/APP_SERVICE_SETUP.md#5-entra-id-easy-auth-の設定)

詳細な環境別構成は [ENVIRONMENTS.md](ENVIRONMENTS.md) を参照してください。

---

## 環境変数

主要な環境変数：

| 変数名 | 説明 | 設定例 |
|--------|------|--------|
| `DEPLOYMENT_SLOT` | 環境識別子 | `development`, `staging`, `production` |
| `ORACLE_DSN` | Oracle接続文字列 | `hostname:port/service_name` |
| `ORACLE_USER` | Oracleユーザー名 | `your_username` |
| `ORACLE_PASSWORD` | Oracleパスワード | `your_password` |
| `SECRET_KEY` | Flaskセッション暗号化キー | ランダム文字列 |

環境別の詳細設定は [ENVIRONMENTS.md](ENVIRONMENTS.md) および [APP_SERVICE_SETUP.md](../environments/APP_SERVICE_SETUP.md) を参照してください。

---

## デプロイメント

### プラットフォーム

- **本番環境**: Azure App Service for Linux
- **地域**: Japan East
- **App Service プラン**: B1以上推奨

### CI/CD

- **推奨方法**: GitHub Actions / Azure DevOps Pipeline
- **デプロイ先**: Stagingスロット → 動作確認 → Productionスワップ

詳細は [APP_SERVICE_SETUP.md](../environments/APP_SERVICE_SETUP.md) を参照してください。

---

**更新日**: 2026-06-17
