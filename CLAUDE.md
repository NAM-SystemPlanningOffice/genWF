1.機能概要
    - システム関係の各種ワークフロー処理
    - 申請業務や承認フローは設定情報をOracleDBに追加することにより柔軟に追加できる設計とします
    - 申請内容やワークフローの進捗状況はOracleDB（TSTCOMDB スキーマNAM_TASK）上で管理します
    - 申請内容が承認された後は出来るだけ自動設定したいので、申請データは可能な範囲で選択子をプルダウンとしたりバリデーションを行ったりします
    - プルダウンの選択肢やバリデーションロジックもOracleDB上で管理します
    - Azure App Service (Linux) 上でPythonでFlaskで構築

2.構成要素
　　A.申請オンライン
      - 申請種類により入力項目等の画面フォーマットが異なる
      - 申請内容が１レコードとなるケースと複数レコードとなるケースがある
      - 既存の申請内容への修正・追加・削除等の場合は既存の内容を参照する（OracleDBへの参照となる）
    B.ワークフローオンライン
      - 申請種類、によって承認フローが異なる
      - デフォルトは申請者を申請対象者とするが、同一所属内であれば他のメンバーの申請も可能
      - 申請対象者の所属長承認は必須
      - 申請種類によっては申請対象オブジェクトの所管の所属長承認が必要となるが、申請対象者の所属＝申請対象オブジェクトの所管の場合は所管承認は省略される
      - 通常はシステム企画室承認が最後の承認となるが、申請種類によって最終承認がシステム開発部長承認となる
      - 申請種類によっては最終承認の前に経営企画部長承認や法務コンプライアンス部長承認等が必要となる場合もある
      - 申請種類によっては最終承認の後に報告が行われる場合があるが、この場合は後続のワークフローや承認の反映処理は報告終了を待つ必要はない
      - 承認ノードは複数のユーザーを含む場合があり、その場合は誰か一人が承認すれば良い
      C. ユーザー情報
        - Oracle DB (TESTCOMDB のnam_user_admin.e_imdb2_users)でユーザーに対する所属の取得が可能
        -　所属には本務と兼務があるが、法務コンプライアンス部（shozoku='2310000'）以外は兼務所属からの申請も可
        - よって、兼務所属がある場合は、自分が申請所属を選択しなければいけない
        -　所属の承認者は TESTCOMDB のnam_ope.e_approver で取得可能、同一所属で複数の承認者がいるので、承認者を選択する必要がある


This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


## 環境構成

### 開発環境（ローカルPC）
- Flask開発サーバー（`python run.py`）
- 手動ログイン（ユーザーID入力）
- 環境変数: `DEPLOYMENT_SLOT=development`

### Staging環境（Azure App Service）
- Azure App Service for Linux
- Gunicorn WSGIサーバー
- Entra ID Easy Auth（SSO）
- Staging用データベース
- 環境変数: `DEPLOYMENT_SLOT=staging`
- セットアップ手順: `docs/APP_SERVICE_SETUP.md`参照

### Production環境（Azure App Service）
- Azure App Service for Linux
- Gunicorn WSGIサーバー
- Entra ID Easy Auth（SSO）
- Production用データベース
- 環境変数: `DEPLOYMENT_SLOT=production`
- セットアップ手順: `docs/APP_SERVICE_SETUP.md`参照

## Getting Started

### 開発環境での起動

```bash
# 仮想環境を有効化
venv\Scripts\activate  # Windows
# または
source venv/bin/activate  # Linux/Mac

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数を設定（.envファイル）
# DEPLOYMENT_SLOT=development

# 開発サーバーを起動（自動リロード有効）
python run.py

# ブラウザでアクセス
# http://localhost:5000/auth/login
# ユーザーIDを入力してログイン
```

### Staging/Production環境でのデプロイ

Azure App Serviceへのデプロイ手順は `docs/APP_SERVICE_SETUP.md` を参照してください。

## 認証方式

| 環境 | 認証方式 | HTTPヘッダー |
|------|---------|-------------|
| **開発環境** | フォーム入力（手動ログイン） | なし |
| **Staging環境** | Entra ID Easy Auth（SSO） | `X-MS-CLIENT-PRINCIPAL-NAME` |
| **Production環境** | Entra ID Easy Auth（SSO） | `X-MS-CLIENT-PRINCIPAL-NAME` |

環境判定: `DEPLOYMENT_SLOT` 環境変数で自動切り替え
