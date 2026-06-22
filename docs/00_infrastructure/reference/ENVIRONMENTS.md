# 環境別構成

本ドキュメントは、GenWFワークフローシステムの環境別構成の**単一情報源（Single Source of Truth）**です。

---

## 環境別仕様表

| 項目 | 開発環境 | Staging環境 | Production環境 |
|------|---------|------------|---------------|
| **実行環境** | ローカルPC | Azure App Service | Azure App Service |
| **Webサーバー** | Flask開発サーバー | Gunicorn | Gunicorn |
| **OS** | Windows/Mac/Linux | Linux (Azure) | Linux (Azure) |
| **認証方式** | 手動ログイン | Entra ID Easy Auth | Entra ID Easy Auth |
| **HTTPヘッダー** | なし | `X-MS-CLIENT-PRINCIPAL-NAME` | `X-MS-CLIENT-PRINCIPAL-NAME` |
| **環境変数: DEPLOYMENT_SLOT** | `development` | `staging` | `production` |
| **データベース** | COMDB | COMDB | COMDB |
| **DBホスト** | com-dbdv | com-dbdv | com-db |
| **スキーマ** | NAM_TASK | NAM_TASK | NAM_TASK |
| **ログレベル** | `INFO`（デフォルト） | `INFO` | `WARNING` |
| **自動リロード** | 有効 | 無効 | 無効 |
| **デバッグモード（Flask DEBUG）** | 有効 | 無効 | 無効 |

---

## 環境判定ロジック

アプリケーションは `DEPLOYMENT_SLOT` 環境変数で実行環境を判定します。

```python
# app/config.py 内の判定例
deployment_slot = os.getenv('DEPLOYMENT_SLOT', 'development')

if deployment_slot == 'development':
    # 開発環境の設定
    DEBUG = True
    # 手動ログイン
elif deployment_slot == 'staging':
    # Staging環境の設定
    DEBUG = False
    # Entra ID Easy Auth
elif deployment_slot == 'production':
    # Production環境の設定
    DEBUG = False
    # Entra ID Easy Auth
```

---

## 開発環境

### 起動方法

```bash
# 仮想環境を有効化
venv\Scripts\activate  # Windows
# または
source venv/bin/activate  # Linux/Mac

# 環境変数を設定（.envファイル）
# DEPLOYMENT_SLOT=development

# 開発サーバーを起動
python run.py

# ブラウザでアクセス
# http://localhost:5000/auth/login
```

### 特徴

- **認証**: ユーザーIDをフォームに入力してログイン
- **自動リロード**: コード変更時に自動的にサーバー再起動
- **デバッグモード**: エラー時に詳細なスタックトレース表示

詳細: [local_testing_guide.md](../local_setup/local_testing_guide.md)

---

## Staging環境

### 用途

- 本番デプロイ前の動作確認
- 統合テスト実行
- ステークホルダーレビュー

### 特徴

- **認証**: Entra ID Easy Auth（SSO）
- **データベース**: COMDB（ホスト: com-dbdv）
- **スキーマ**: NAM_TASK
- **デプロイ**: GitHub Actions / Azure CLIで自動/手動デプロイ

### アクセス

- URL: `https://<app-name>-staging.azurewebsites.net`
- 認証: Microsoft Entra IDアカウント

詳細: [APP_SERVICE_SETUP.md](../environments/APP_SERVICE_SETUP.md)

---

## Production環境

### 用途

- 本番運用環境
- エンドユーザーが実際に使用

### 特徴

- **認証**: Entra ID Easy Auth（SSO）
- **データベース**: COMDB（ホスト: com-db）
- **スキーマ**: NAM_TASK
- **デプロイ**: Stagingスロット検証後、スワップでデプロイ

### アクセス

- URL: `https://<app-name>.azurewebsites.net`
- 認証: Microsoft Entra IDアカウント

### デプロイフロー

```
[開発環境]
   ↓ git push
[GitHub]
   ↓ デプロイ
[Staging スロット] ← 動作確認
   ↓ スワップ
[Production スロット]
```

詳細: [APP_SERVICE_SETUP.md](../environments/APP_SERVICE_SETUP.md)

---

## 環境別設定ファイル

### .env（開発環境のみ）

```bash
DEPLOYMENT_SLOT=development
ORACLE_DSN=com-dbdv:1521/COMDB
ORACLE_USER=NAM_TASK
ORACLE_PASSWORD=your_password
SECRET_KEY=your-secret-key-here
```

**重要**: `.env` ファイルは `.gitignore` に含まれており、Gitにコミットされません。

**データベース接続情報**:
- **データベース**: `COMDB` (全環境共通のSID)
- **スキーマ**: `NAM_TASK` (全環境共通)
- **開発/Staging環境**: ホスト `com-dbdv`、ポート `1521`、DSN `com-dbdv:1521/COMDB`
- **Production環境**: ホスト `com-db`、ポート `1521`、DSN `com-db:1521/COMDB`

**DSN形式**: `hostname:port/sid_or_service_name` (python-oracledb Easy Connect形式)

### Azure App Service構成（Staging/Production）

Azure Portal: **設定** → **構成** → **アプリケーション設定**

スロット別設定として以下を構成：
- `DEPLOYMENT_SLOT`
- `ORACLE_DSN`
- `ORACLE_USER`
- `ORACLE_PASSWORD`

詳細: [APP_SERVICE_SETUP.md](../environments/APP_SERVICE_SETUP.md#3-環境変数の設定)

---

## 関連ドキュメント

- [技術仕様](TECH_SPECS.md) - Python/Flask/DBのバージョン情報
- [ディレクトリ構成](DIRECTORY_STRUCTURE.md) - プロジェクト構造
- [App Service セットアップ](../environments/APP_SERVICE_SETUP.md) - Azure環境構築手順
- [ローカルテストガイド](../local_setup/local_testing_guide.md) - 開発環境でのテスト実行

---

**更新日**: 2026-06-17
