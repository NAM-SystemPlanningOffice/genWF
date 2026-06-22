# JSON申請データ自動取り込み機能 設計仕様書

**作成日**: 2026-06-08  
**バージョン**: 1.0  
**ステータス**: 設計完了（未実装）

---

## 1. 機能概要

外部システムやバッチ処理から申請データをJSON形式で受け取り、自動的に申請データを作成してワークフローを開始する機能です。

### 1.1 主な特徴

- JSONファイルを指定フォルダに配置することで自動処理を開始
- バリデーションを実行し、エラーがあればエラーログを出力
- 成功時は申請IDとワークフローインスタンスIDを返却
- 承認者は自動選択（申請種類とユーザー所属から自動決定）
- 非同期処理（バックグラウンドで実行可能）

### 1.2 運用イメージ

- **初回申請**: JSON経由で自動登録し、ワークフロー開始
- **差し戻し時**: 申請者（`applicant_user_id`）がWeb UIにログインして修正・再提出
- **承認者選択**: システムが自動選択（ユーザーによる手動指定は不要）

---

## 2. JSONファイル仕様

### 2.1 基本構造（単一レコード申請）

```json
{
  "meta": {
    "request_id": "REQ-20260608-001",
    "application_type_code": "APP_TYPE_001",
    "action_type": "create",
    "applicant_user_id": "U12345",
    "applicant_shozoku": "2100000",
    "application_title": "新規アカウント申請",
    "resource_id": "RES_12345",
    "remarks": "自動申請バッチより",
    "scheduled_date": "2026-06-15"
  },
  "fields": [
    {
      "field_code": "user_name",
      "field_value": "山田太郎",
      "field_label": "山田太郎"
    },
    {
      "field_code": "email",
      "field_value": "yamada@example.com"
    },
    {
      "field_code": "department_code",
      "field_value": "2100000",
      "field_label": "システム企画室"
    }
  ]
}
```

### 2.2 複数レコード申請

```json
{
  "meta": {
    "request_id": "REQ-20260608-002",
    "application_type_code": "MULTI_MEMBER_ADD",
    "action_type": "modify",
    "applicant_user_id": "U12345",
    "applicant_shozoku": "2100000",
    "application_title": "メンバー一括追加申請",
    "resource_id": "PROJECT_001",
    "remarks": "定期メンテナンスバッチより"
  },
  "records": [
    {
      "action": "add",
      "fields": [
        {
          "field_code": "member_user_id",
          "field_value": "U67890",
          "field_label": "佐藤花子"
        },
        {
          "field_code": "role",
          "field_value": "member",
          "field_label": "メンバー"
        }
      ]
    },
    {
      "action": "modify",
      "fields": [
        {
          "field_code": "member_user_id",
          "field_value": "U11111",
          "field_label": "鈴木次郎"
        },
        {
          "field_code": "role",
          "field_value": "admin",
          "field_label": "管理者"
        }
      ]
    },
    {
      "action": "delete",
      "fields": [
        {
          "field_code": "member_user_id",
          "field_value": "U22222",
          "field_label": "田中三郎"
        }
      ]
    }
  ]
}
```

### 2.3 メタデータフィールド定義

| フィールド | 必須 | データ型 | 説明 |
|-----------|------|---------|------|
| `meta.request_id` | 任意 | 文字列 | リクエスト識別子（処理追跡用、重複チェックに使用可能）<br>推奨形式: `REQ-YYYYMMDD-NNN` |
| `meta.application_type_code` | 必須 | 文字列 | 申請種類コード（M_APPLICATION_TYPE.application_type_code） |
| `meta.action_type` | 必須 | 文字列 | アクション種別（`create`/`modify`/`delete`） |
| `meta.applicant_user_id` | 必須 | 文字列 | 申請者ユーザーID（実在の担当者、差し戻し時に修正を行う） |
| `meta.applicant_shozoku` | 必須 | 文字列 | 申請者所属コード（兼務所属も指定可能） |
| `meta.application_title` | 必須 | 文字列 | 申請タイトル（承認画面・一覧画面に表示） |
| `meta.resource_id` | 任意 | 文字列 | リソースID（T_APPLICATION.reference_resource_idにセット）<br>対象リソースの識別、承認後の自動処理で参照 |
| `meta.jurisdiction_shozoku` | 任意 | 文字列 | 所管所属コード（未指定時は申請種類の設定に従って自動判定） |
| `meta.scheduled_date` | 任意 | 文字列 | 適用予定日（ISO 8601形式: `YYYY-MM-DD`） |
| `meta.remarks` | 任意 | 文字列 | 備考（申請詳細画面に表示） |

### 2.4 フィールドデータ定義

#### 2.4.1 単一レコード申請の場合

| フィールド | 必須 | データ型 | 説明 |
|-----------|------|---------|------|
| `fields` | 必須 | 配列 | フィールド値の配列 |
| `fields[].field_code` | 必須 | 文字列 | フィールドコード（M_APPLICATION_FIELD.field_code） |
| `fields[].field_value` | 必須 | 文字列 | フィールド値 |
| `fields[].field_label` | 任意 | 文字列 | 表示用ラベル（プルダウン選択時の表示名）<br>未指定時はfield_valueを表示 |

#### 2.4.2 複数レコード申請の場合

| フィールド | 必須 | データ型 | 説明 |
|-----------|------|---------|------|
| `records` | 必須 | 配列 | レコードの配列 |
| `records[].action` | 必須 | 文字列 | レコード操作（`add`/`modify`/`delete`） |
| `records[].fields` | 必須 | 配列 | フィールド値の配列 |
| `records[].fields[].field_code` | 必須 | 文字列 | フィールドコード |
| `records[].fields[].field_value` | 必須 | 文字列 | フィールド値 |
| `records[].fields[].field_label` | 任意 | 文字列 | 表示用ラベル |

---

## 3. トリガー方式

### 3.1 ファイル監視方式（推奨）

#### 3.1.1 フォルダ構成

```
c:\genWF_data\import\
  ├── inbox\         # 処理待ちJSONファイル配置
  ├── processing\    # 処理中ファイル移動先
  ├── completed\     # 処理完了ファイル移動先
  └── error\         # エラーファイル移動先
```

#### 3.1.2 動作フロー

1. Windowsタスクスケジューラで定期実行（例: 5分毎）
2. `inbox`フォルダ内の`*.json`ファイルを検出
3. ファイルを`processing`へ移動
4. 処理実行
5. 成功時: `completed`へ移動 + `.result.json`を出力
6. 失敗時: `error`へ移動 + `.error.json`を出力

#### 3.1.3 タスクスケジューラ設定例

```powershell
# タスク名: GenWF_JSONImport
# トリガー: 5分毎
# 操作: python c:\Users\ootagaki\claude1\genWF\batch\import_applications.py
```

### 3.2 REST API方式（将来拡張）

#### 3.2.1 エンドポイント

```
POST /api/import/application
Content-Type: application/json

{
  ... (上記JSON仕様と同じ)
}
```

#### 3.2.2 レスポンス

**成功時:**
```json
{
  "success": true,
  "application_id": 12345,
  "workflow_instance_id": 67890,
  "message": "申請を作成し、ワークフローを開始しました"
}
```

**失敗時:**
```json
{
  "success": false,
  "error_type": "validation_error",
  "errors": [
    {
      "field": "email",
      "message": "メールアドレスの形式が不正です"
    }
  ]
}
```

### 3.3 コマンドライン方式

```bash
# 単一ファイル処理
python batch/import_applications.py --file c:\path\to\application.json

# フォルダ一括処理
python batch/import_applications.py --dir c:\genWF_data\import\inbox
```

---

## 4. 処理フロー

```
[JSONファイル配置]
    ↓
[ファイル検出・移動（inbox → processing）]
    ↓
[JSON構文チェック]
    ↓
[メタデータ検証]
    - application_type_code存在チェック
    - applicant_user_id存在チェック
    - applicant_shozoku妥当性チェック
    - action_type妥当性チェック
    ↓
[申請可能性チェック]
    - ApplicationType.is_allowed_to_apply()
    - 申請種別のサポート状況確認
    ↓
[フィールドマッピング]
    - field_codeからfield_idへ変換
    - プルダウン選択肢の妥当性確認
    ↓
[jurisdiction_shozoku自動判定]
    - 未指定かつresource_idがある場合
    - resource_jurisdiction_columnから取得
    ↓
[バリデーション実行]
    - ValidationService.validate_field()
    - 全バリデーションルールを適用
    ↓
[下書き申請作成]
    - Application.create()
      └─ reference_resource_id に resource_id をセット
    - ApplicationDetail.save_details()
    ↓
[ワークフロー開始]
    - WorkflowService.start_workflow()
      └─ 承認者は自動選択（selected_approvers=None）
    ↓
[結果出力]
    - 成功: *.result.json生成 + completedへ移動
    - 失敗: *.error.json生成 + errorへ移動
```

---

## 5. 出力ファイル仕様

### 5.1 成功時（*.result.json）

**ファイル名**: 元のファイル名 + `.result.json`  
**例**: `REQ-20260608-001.json` → `REQ-20260608-001.json.result.json`

```json
{
  "success": true,
  "request_id": "REQ-20260608-001",
  "application_id": 12345,
  "workflow_instance_id": 67890,
  "application_status": "submitted",
  "created_at": "2026-06-08T10:30:00+09:00",
  "message": "申請を作成し、ワークフローを開始しました"
}
```

### 5.2 失敗時（*.error.json）

**ファイル名**: 元のファイル名 + `.error.json`  
**例**: `REQ-20260608-001.json` → `REQ-20260608-001.json.error.json`

```json
{
  "success": false,
  "request_id": "REQ-20260608-001",
  "error_type": "validation_error",
  "errors": [
    {
      "field": "email",
      "message": "メールアドレスの形式が不正です"
    },
    {
      "field": "user_name",
      "message": "必須項目です"
    }
  ],
  "processed_at": "2026-06-08T10:30:00+09:00"
}
```

### 5.3 エラー種別一覧

| error_type | 説明 | 対応方法 |
|-----------|------|---------|
| `json_syntax_error` | JSON構文エラー | JSONフォーマットを修正 |
| `schema_error` | JSON構造エラー（必須項目不足等） | 必須項目を追加 |
| `application_type_not_found` | 申請種類が見つからない | application_type_codeを確認 |
| `user_not_found` | ユーザーが見つからない | applicant_user_idを確認 |
| `shozoku_not_found` | 所属が見つからない | applicant_shozokuを確認 |
| `permission_denied` | 申請権限なし | 申請可能制限を確認 |
| `field_not_found` | フィールドが見つからない | field_codeを確認 |
| `validation_error` | フィールドバリデーションエラー | エラー内容に従って修正 |
| `workflow_error` | ワークフロー開始エラー | ワークフロー定義を確認 |
| `system_error` | システムエラー | ログを確認、管理者に連絡 |
| `duplicate_request` | request_idが重複 | 既に処理済み、無視してよい |

---

## 6. resource_id の活用

### 6.1 T_APPLICATIONへの保存

`meta.resource_id` は `T_APPLICATION.reference_resource_id` に保存されます。

```sql
SELECT 
  application_id,
  application_title,
  reference_resource_id,  -- ← ここに保存
  application_status
FROM T_APPLICATION
WHERE application_id = 12345;
```

### 6.2 活用例

#### 例1: 修正申請での対象リソース明示

```json
{
  "meta": {
    "application_type_code": "DB_USER_MODIFY",
    "action_type": "modify",
    "resource_id": "DBUSER_YAMADA",
    ...
  }
}
```
→ 申請詳細画面で「対象リソース: DBUSER_YAMADA」と表示  
→ 承認者が修正対象を明確に把握できる

#### 例2: 削除申請

```json
{
  "meta": {
    "application_type_code": "PROJECT_DELETE",
    "action_type": "delete",
    "resource_id": "PROJECT_001",
    ...
  }
}
```
→ 承認者が「どのプロジェクトを削除する申請か」を明確に把握

#### 例3: 承認後の自動処理での参照

```python
# 承認完了時の自動処理
application = Application.get_by_id(application_id)
resource_id = application.get('reference_resource_id')

if resource_id:
    # リソースIDを使って自動設定を実行
    execute_provisioning(resource_id, application_details)
```

### 6.3 jurisdiction_shozoku の自動判定

`resource_id` が指定され、かつ `jurisdiction_shozoku` が未指定の場合、申請種類の設定に基づいて自動判定されます。

**前提条件:**
- `M_APPLICATION_TYPE.resource_detail_query` が設定されている
- `M_APPLICATION_TYPE.resource_jurisdiction_column` が設定されている

**動作:**
1. `resource_detail_query` を実行して対象リソースの詳細を取得
2. `resource_jurisdiction_column` で指定されたカラムから所管所属を取得
3. `T_APPLICATION.jurisdiction_shozoku` にセット

---

## 7. 差し戻し時の運用フロー

```
[差し戻し発生]
    ↓
[担当者（applicant_user_id）にメール通知]
    ↓
[担当者がWeb UIにログイン]
    ↓
[タスク一覧で下書き状態の申請を確認]
    ↓
[編集画面で内容を修正]
    ↓
[提出ボタン押下]
    ↓
[バリデーション実行]
    ↓
[承認者選択画面]
    - 承認者候補が1名 → 自動選択してワークフロー開始
    - 承認者候補が複数 → ユーザーが選択
    ↓
[ワークフロー再開]
```

**ポイント:**
- JSON自動取り込みは「初回申請の効率化」が目的
- 差し戻し後は通常のWeb UI操作フローで対応
- 担当者が内容を確認・修正できるため安全

---

## 8. 実装ファイル構成

### 8.1 ディレクトリ構造

```
genWF/
├── batch/
│   ├── import_applications.py      # メインバッチスクリプト
│   └── import_config.json          # 設定ファイル
├── app/
│   └── services/
│       └── import_service.py       # インポートサービス（共通ロジック）
├── data/
│   └── import/
│       ├── inbox/
│       ├── processing/
│       ├── completed/
│       └── error/
└── logs/
    └── import_YYYYMMDD.log         # 処理ログ
```

### 8.2 主要モジュール

#### 8.2.1 batch/import_applications.py

- ファイル監視とディスパッチ
- コマンドライン引数処理
- ファイル移動処理
- 結果ファイル出力

#### 8.2.2 app/services/import_service.py

- JSON解析とバリデーション
- Application/ApplicationDetail作成
- WorkflowService呼び出し
- エラーハンドリング

### 8.3 import_config.json（設定例）

```json
{
  "watch_interval_seconds": 300,
  "inbox_dir": "c:\\genWF_data\\import\\inbox",
  "processing_dir": "c:\\genWF_data\\import\\processing",
  "completed_dir": "c:\\genWF_data\\import\\completed",
  "error_dir": "c:\\genWF_data\\import\\error",
  "enable_duplicate_check": true,
  "log_level": "INFO"
}
```

---

## 9. セキュリティ・運用考慮事項

### 9.1 重複処理防止

**方法1: request_id による重複チェック**

T_APPLICATIONにカラム追加（推奨）:

```sql
ALTER TABLE T_APPLICATION ADD import_request_id VARCHAR2(100);
CREATE INDEX idx_app_request_id ON T_APPLICATION(import_request_id);
```

処理前にチェック:

```python
request_id = json_data['meta'].get('request_id')
if request_id and Application.exists_by_request_id(request_id):
    raise DuplicateRequestError(f"Request ID {request_id} は既に処理済みです")
```

**方法2: ファイル名にタイムスタンプを含める**

推奨ファイル名形式: `{request_id}_{timestamp}.json`  
例: `REQ-20260608-001_20260608103000.json`

### 9.2 エラーハンドリング

- 処理中にシステムエラーが発生した場合、ファイルを`error`へ移動
- リトライロジックは実装せず、手動再配置で対応
- トランザクションをロールバックし、部分的な申請作成を防止

### 9.3 ログ出力

**ログファイル**: `logs/import_YYYYMMDD.log`

**ログレベル**:
- `INFO`: 処理開始/終了、成功
- `WARNING`: バリデーションエラー、スキップ
- `ERROR`: システムエラー（スタックトレース含む）

**ログ例**:
```
2026-06-08 10:30:00 INFO  [import] Processing: REQ-20260608-001.json
2026-06-08 10:30:05 INFO  [import] Application created: application_id=12345
2026-06-08 10:30:10 INFO  [import] Workflow started: workflow_instance_id=67890
2026-06-08 10:30:15 INFO  [import] Success: REQ-20260608-001.json
```

### 9.4 承認者自動選択

- 承認者候補が所属から自動取得される
- 候補が複数いる場合は先頭の承認者を自動選択
- 候補がいない場合はエラー（workflow_error）

### 9.5 バリデーション

- すべてのフィールドについて定義済みバリデーションルールを適用
- バリデーションスキップ機能は実装しない（セキュリティリスク）

---

## 10. 将来の拡張性

### 10.1 REST API化

- Azure App Service経由でHTTP POSTを受け付け
- Entra ID認証との連携
- リアルタイム処理

### 10.2 メッセージキュー連携

- Azure Service Bus
- RabbitMQ
- 大量申請の処理

### 10.3 再提出専用API

差し戻された申請を自動で再提出:

```json
{
  "meta": {
    "operation": "resubmit",
    "application_id": 12345
  },
  "fields": [
    {
      "field_code": "email",
      "field_value": "new-email@example.com"
    }
  ]
}
```

### 10.4 ステータス照会API

```
GET /api/import/status/{request_id}

Response:
{
  "request_id": "REQ-20260608-001",
  "status": "submitted",
  "application_id": 12345,
  "workflow_instance_id": 67890
}
```

---

## 11. 実装時のチェックリスト

### 11.1 DB準備

- [ ] T_APPLICATIONにimport_request_idカラム追加（任意）
- [ ] インデックス作成

### 11.2 ファイル・フォルダ準備

- [ ] `c:\genWF_data\import\inbox` 作成
- [ ] `c:\genWF_data\import\processing` 作成（Windows）または `/home/genWF_data/import/processing`（Linux）
- [ ] `c:\genWF_data\import\completed` 作成（Windows）または `/home/genWF_data/import/completed`（Linux）
- [ ] `c:\genWF_data\import\error` 作成（Windows）または `/home/genWF_data/import/error`（Linux）
- [ ] アクセス権限設定（App Serviceのアプリケーションユーザー）

### 11.3 コード実装

- [ ] `batch/import_applications.py` 作成
- [ ] `app/services/import_service.py` 作成
- [ ] `batch/import_config.json` 作成
- [ ] ユニットテスト作成

### 11.4 テスト

- [ ] 単一レコード申請のテスト
- [ ] 複数レコード申請のテスト
- [ ] バリデーションエラーのテスト
- [ ] 重複チェックのテスト
- [ ] エラーハンドリングのテスト

### 11.5 運用準備

- [ ] Windowsタスクスケジューラ設定
- [ ] 運用マニュアル作成
- [ ] エラー発生時の対応手順作成

---

## 12. 参考資料

- [CLAUDE.md](../CLAUDE.md) - システム全体の機能概要
- [database_design.md](database_design.md) - DB設計
- [VALIDATION_RULES.md](VALIDATION_RULES.md) - バリデーションルール
- [WORKFLOW_NODE_TYPES.md](WORKFLOW_NODE_TYPES.md) - ワークフロー定義

---

**変更履歴**

| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| 1.0 | 2026-06-08 | 初版作成 |
