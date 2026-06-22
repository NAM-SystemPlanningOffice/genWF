# Azure App Service セットアップ手順

Azure App Service for Linux上でGenWFワークフローシステムをデプロイする手順です。

> **環境構成**: 環境別の詳細な構成は [../reference/ENVIRONMENTS.md](../reference/ENVIRONMENTS.md) を参照してください。  
> **技術仕様**: Python/データベース等の詳細は [../reference/TECH_SPECS.md](../reference/TECH_SPECS.md) を参照してください。

## 前提条件

- Azureサブスクリプション
- Azure CLI または Azure Portal へのアクセス
- Git リポジトリ（GitHub、Azure Repos など）
- Oracle Database への接続情報

## アーキテクチャ概要

```
[開発環境]
  ↓ git push
[GitHub/Azure Repos]
  ↓ デプロイ
[Azure App Service - Staging Slot]
  - Entra ID Easy Auth
  - Gunicorn + Flask
  - Staging DB接続
  ↓ スワップ
[Azure App Service - Production Slot]
  - Entra ID Easy Auth
  - Gunicorn + Flask
  - Production DB接続
```

---

## 1. Azure App Serviceリソースの作成


### Azure Portalでの作成

1. **リソースの作成** → **Web App**
2. 基本設定:
   - リソースグループ: 新規作成または既存を選択
   - 名前: `genWF-app`（グローバルに一意）
   - 公開: コード
   - ランタイムスタック: Python 3.13（プロジェクト標準バージョン）
   - オペレーティングシステム: Linux
   - 地域: Japan East
   - App Service プラン: B1以上推奨

---

## 2. Stagingスロットの作成

### Azure CLIでの作成

```bash
# Stagingスロット作成
az webapp deployment slot create \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging
```

### Azure Portalでの作成

1. App Service → **デプロイ** → **デプロイスロット**
2. **スロットの追加**
3. 名前: `staging`
4. 設定の複製元: なし（または既存のスロット）

---

## 3. 環境変数の設定

### スロット別設定（スワップされない設定）

各スロットで個別に設定します。

#### Productionスロット

Azure Portal: **設定** → **構成** → **アプリケーション設定**

| 名前 | 値 | スロット設定 |
|------|-----|------------|
| `DEPLOYMENT_SLOT` | `production` | ✅ チェック |
| `ORACLE_DSN` | `com-db:1521/COMDB` | ✅ チェック |
| `ORACLE_USER` | `NAM_TASK` | ✅ チェック |
| `ORACLE_PASSWORD` | `production-password` | ✅ チェック |
| `LOG_LEVEL` | `WARNING` | ✅ チェック |

**スロット設定**: デプロイスロット設定にチェックを入れると、スワップ時に設定が移動しません。

#### Stagingスロット

Azure Portal: **デプロイスロット** → **staging** → **設定** → **構成**

| 名前 | 値 | スロット設定 |
|------|-----|------------|
| `DEPLOYMENT_SLOT` | `staging` | ✅ チェック |
| `ORACLE_DSN` | `com-dbdv:1521/COMDB` | ✅ チェック |
| `ORACLE_USER` | `NAM_TASK` | ✅ チェック |
| `ORACLE_PASSWORD` | `staging-password` | ✅ チェック |
| `LOG_LEVEL` | `INFO` | ✅ チェック |

### 共通設定（スワップされる設定）

Productionスロットで設定（Stagingにも自動的に適用されます）

| 名前 | 値 | スロット設定 |
|------|-----|------------|
| `SECRET_KEY` | `your-secret-key-here` | ❌ チェックなし |
| `ITEMS_PER_PAGE` | `20` | ❌ チェックなし |
| `MAX_UPLOAD_SIZE` | `10485760` | ❌ チェックなし |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | ❌ チェックなし |

### Azure CLIでの設定

```bash
# Productionスロット（スロット固有設定）
az webapp config appsettings set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    DEPLOYMENT_SLOT=production \
    ORACLE_DSN="com-db:1521/COMDB" \
    ORACLE_USER="NAM_TASK" \
    ORACLE_PASSWORD="production-password" \
    LOG_LEVEL="WARNING" \
  --slot-settings DEPLOYMENT_SLOT ORACLE_DSN ORACLE_USER ORACLE_PASSWORD LOG_LEVEL

# Stagingスロット（スロット固有設定）
az webapp config appsettings set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging \
  --settings \
    DEPLOYMENT_SLOT=staging \
    ORACLE_DSN="com-dbdv:1521/COMDB" \
    ORACLE_USER="NAM_TASK" \
    ORACLE_PASSWORD="staging-password" \
    LOG_LEVEL="INFO" \
  --slot-settings DEPLOYMENT_SLOT ORACLE_DSN ORACLE_USER ORACLE_PASSWORD LOG_LEVEL

# 共通設定（Productionスロットで設定）
az webapp config appsettings set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    SECRET_KEY="your-secret-key-here" \
    ITEMS_PER_PAGE=20 \
    MAX_UPLOAD_SIZE=10485760 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

---

## 4. Entra ID Easy Auth（認証）の設定

### Productionスロット

1. Azure Portal → App Service → **設定** → **認証**
2. **ID プロバイダーの追加**
3. ID プロバイダー: **Microsoft**
4. アプリ登録の種類: **新しいアプリ登録を作成する**
5. 名前: `genWF-app-auth`
6. サポートされているアカウントの種類: **現在のテナントのみ（シングルテナント）**
7. 認証されていない要求: **HTTP 401 未承認: API 用に推奨**
8. トークンストア: **有効**
9. 保存

### Stagingスロット

1. **デプロイスロット** → **staging** → **設定** → **認証**
2. 上記と同じ手順で設定
3. アプリ登録名: `genWF-app-staging-auth`

### 動作確認

ブラウザで以下のURLにアクセス：

- Production: `https://genWF-app.azurewebsites.net/auth/login`
- Staging: `https://genWF-app-staging.azurewebsites.net/auth/login`

→ Entra IDログイン画面にリダイレクトされることを確認

---

## 5. アプリケーションのデプロイ

### 方法1: GitHub Actionsによる自動デプロイ（推奨）

#### デプロイセンターの設定

1. Azure Portal → App Service → **デプロイ** → **デプロイセンター**
2. ソース: **GitHub**
3. 組織・リポジトリ・ブランチを選択
4. ビルドプロバイダー: **GitHub Actions**
5. 保存

自動的に `.github/workflows/azure-webapps-python.yml` が生成されます。

#### ワークフローのカスタマイズ（必要に応じて）

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches:
      - main  # mainブランチへのpushでproductionにデプロイ
      - staging  # stagingブランチへのpushでstagingスロットにデプロイ

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Deploy to Azure Web App (Staging)
        if: github.ref == 'refs/heads/staging'
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'genWF-app'
          slot-name: 'staging'
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_STAGING }}

      - name: Deploy to Azure Web App (Production)
        if: github.ref == 'refs/heads/main'
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'genWF-app'
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

### 方法2: Azure CLIによる手動デプロイ

```bash
# Git経由でデプロイ（Staging）
az webapp deployment source config-local-git \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging

# リモートリポジトリのURLを取得
az webapp deployment list-publishing-credentials \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging \
  --query scmUri \
  --output tsv

# Gitでプッシュ
git remote add azure-staging <上記で取得したURL>
git push azure-staging main:master
```

### 方法3: ZIPデプロイ

```bash
# アプリケーションをZIP化
zip -r genWF.zip . -x "venv/*" ".git/*" "__pycache__/*" "*.pyc"

# Stagingスロットにデプロイ
az webapp deployment source config-zip \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging \
  --src genWF.zip
```

---

## 6. 起動コマンドの設定

App Serviceが正しく起動スクリプトを実行するよう設定します。

### Azure Portal

1. **設定** → **構成** → **全般設定**
2. スタートアップコマンド: `bash startup.sh`
3. 保存

### Azure CLI

```bash
# Stagingスロット
az webapp config set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging \
  --startup-file "bash startup.sh"

# Productionスロット
az webapp config set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "bash startup.sh"
```

---

## 7. ログとモニタリング

### アプリケーションログの有効化

```bash
# アプリケーションログを有効化
az webapp log config \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --application-logging filesystem \
  --detailed-error-messages true \
  --failed-request-tracing true \
  --web-server-logging filesystem
```

### ログのストリーミング表示

```bash
# Productionスロット
az webapp log tail \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Stagingスロット
az webapp log tail \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging
```

### Azure Portalでログ確認

1. App Service → **監視** → **ログストリーム**
2. リアルタイムでアプリケーションログを確認

---

## 8. スロットスワップ（Staging → Production）

### スワップ前の確認事項

1. ✅ Stagingスロットでの動作確認
2. ✅ データベース接続確認
3. ✅ Entra ID認証の動作確認
4. ✅ パフォーマンステスト
5. ✅ エラーログの確認

### Azure Portalでスワップ

1. App Service → **デプロイ** → **デプロイスロット**
2. **スワップ**をクリック
3. ソース: `staging`
4. ターゲット: `production`
5. **スワップの開始**

### Azure CLIでスワップ

```bash
az webapp deployment slot swap \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging \
  --target-slot production
```

### スワップのロールバック

問題が発生した場合は逆方向にスワップ：

```bash
az webapp deployment slot swap \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot production \
  --target-slot staging
```

---

## 9. トラブルシューティング

### アプリケーションが起動しない

```bash
# ログを確認
az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP

# SSHでコンテナに接続（診断用）
az webapp ssh --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP
```

### 確認ポイント
1. `startup.sh` の実行権限: `chmod +x startup.sh`
2. `requirements.txt` のインストール成功
3. `DEPLOYMENT_SLOT` 環境変数の設定
4. Oracle DB接続情報の正確性

### Entra ID認証が動作しない

1. **認証設定の確認**
   - Azure Portal → App Service → 認証
   - ID プロバイダーが正しく設定されているか

2. **ヘッダーの確認**
   - ログに `X-MS-CLIENT-PRINCIPAL-NAME` ヘッダーが表示されているか
   - Easy Authが有効で、ユーザーがログイン済みか

3. **リダイレクトURIの確認**
   - Entra IDアプリ登録のリダイレクトURIに、App ServiceのURLが含まれているか

### データベース接続エラー

```bash
# 環境変数の確認
az webapp config appsettings list \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging
```

- `ORACLE_DSN` の形式: `hostname:port/service_name`
- ネットワークセキュリティグループ（NSG）でOracle DBへのアクセスが許可されているか
- App ServiceのVNet統合が必要な場合は設定

---

## 10. セキュリティ設定（推奨）

### HTTPSの強制

```bash
az webapp update \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --https-only true
```

### 最小TLSバージョンの設定

```bash
az webapp config set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --min-tls-version 1.2
```

### アクセス制限（必要に応じて）

特定IPアドレスからのアクセスのみ許可：

```bash
az webapp config access-restriction add \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --rule-name "AllowOfficeIP" \
  --action Allow \
  --ip-address "203.0.113.0/24" \
  --priority 100
```

---

## 11. スケーリング設定

### 手動スケールアウト

```bash
az appservice plan update \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --number-of-workers 3
```

### 自動スケーリング（S1以上のプラン）

Azure Portal → App Service Plan → **スケールアウト** → **カスタム自動スケーリング**

ルール例:
- CPU使用率 > 70% → インスタンス追加
- CPU使用率 < 30% → インスタンス削減
- 最小インスタンス数: 2
- 最大インスタンス数: 10

---

## 12. 参考資料

- [Azure App Service ドキュメント](https://learn.microsoft.com/ja-jp/azure/app-service/)
- [Python on App Service](https://learn.microsoft.com/ja-jp/azure/app-service/configure-language-python)
- [Entra ID Easy Auth](https://learn.microsoft.com/ja-jp/azure/app-service/overview-authentication-authorization)
- [デプロイスロット](https://learn.microsoft.com/ja-jp/azure/app-service/deploy-staging-slots)
- [Gunicorn ドキュメント](https://docs.gunicorn.org/)
