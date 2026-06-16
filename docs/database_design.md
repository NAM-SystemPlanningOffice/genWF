# Oracleデータベース設計

## データベース情報
- **データベース**: TSTCOMDB
- **スキーマ**: NAM_TASK
- **既存参照スキーマ**: nam_user_admin, nam_ope

## テーブル設計概要

### 1. 申請管理テーブル

#### T_APPLICATION (申請マスタ)
申請の基本情報を管理する。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| application_id | NUMBER | PK | 申請ID（シーケンスで自動採番） |
| application_type_id | NUMBER | FK, NOT NULL | 申請種類ID |
| action_type | VARCHAR2(20) | NOT NULL | 申請区分（create/modify/delete） |
| applicant_user_id | VARCHAR2(50) | NOT NULL | 申請者のユーザーID |
| applicant_shozoku | VARCHAR2(20) | NOT NULL | 申請者の申請時所属コード |
| target_user_id | VARCHAR2(50) | | 申請対象者のユーザーID（ユーザーに関わる申請の場合のみ） |
| target_shozoku | VARCHAR2(20) | | 申請対象者の所属コード（ユーザーに関わる申請の場合のみ） |
| jurisdiction_shozoku | VARCHAR2(20) | | 申請対象リソースの所管所属コード |
| application_title | VARCHAR2(200) | NOT NULL | 申請タイトル |
| application_status | VARCHAR2(20) | NOT NULL | 申請ステータス（draft/submitted/approved/rejected/withdrawn） |
| current_workflow_node_id | NUMBER | FK | 現在の承認ノードID |
| reference_resource_id | VARCHAR2(200) | | 参照リソースID（修正・削除時の対象リソース識別子） |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |
| submitted_at | TIMESTAMP | | 提出日時 |
| completed_at | TIMESTAMP | | 完了日時 |
| remarks | CLOB | | 備考 |

**インデックス**:
- `IDX_APP_STATUS` (application_status)
- `IDX_APP_TYPE` (application_type_id)
- `IDX_APP_ACTION` (action_type)
- `IDX_APP_APPLICANT` (applicant_user_id)
- `IDX_APP_TARGET` (target_user_id)
- `IDX_APP_JURIS` (jurisdiction_shozoku)
- `IDX_APP_REF_RESOURCE` (reference_resource_id)

**補足説明**:
- `target_user_id`と`target_shozoku`は、申請種類が「ユーザーに関わる申請」の場合のみ入力される
- `jurisdiction_shozoku`は、申請対象リソース（Gmailグループ、データベース等）の所管所属を格納
- 所管承認の要否判定に使用（applicant_shozoku ≠ jurisdiction_shozokuの場合は所管承認が必要）

#### T_APPLICATION_DETAIL (申請詳細)
申請の詳細データを保持する（EAVモデル）。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| detail_id | NUMBER | PK | 詳細ID（シーケンスで自動採番） |
| application_id | NUMBER | FK, NOT NULL | 申請ID |
| detail_seq | NUMBER | NOT NULL | 明細連番（複数レコード対応） |
| field_id | NUMBER | FK, NOT NULL | フィールドID |
| field_value | VARCHAR2(4000) | | フィールド値 |
| field_value_large | CLOB | | 大容量フィールド値 |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

**ユニーク制約**: (application_id, detail_seq, field_id)

**インデックス**:
- `IDX_DETAIL_APP` (application_id)

---

### 2. ワークフロー管理テーブル

#### T_WORKFLOW_INSTANCE (ワークフローインスタンス)
各申請のワークフロー実行インスタンスを管理。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| workflow_instance_id | NUMBER | PK | ワークフローインスタンスID |
| application_id | NUMBER | FK, NOT NULL, UNIQUE | 申請ID |
| workflow_definition_id | NUMBER | FK, NOT NULL | ワークフロー定義ID |
| current_node_seq | NUMBER | NOT NULL | 現在のノード順序番号 |
| workflow_status | VARCHAR2(20) | NOT NULL | ワークフローステータス（in_progress/completed/rejected） |
| started_at | TIMESTAMP | NOT NULL | 開始日時 |
| completed_at | TIMESTAMP | | 完了日時 |

**インデックス**:
- `IDX_WF_INST_APP` (application_id)
- `IDX_WF_INST_STATUS` (workflow_status)

#### T_WORKFLOW_NODE_INSTANCE (ワークフローノードインスタンス)
ワークフローの各承認ノードの実行状態を管理。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| node_instance_id | NUMBER | PK | ノードインスタンスID |
| workflow_instance_id | NUMBER | FK, NOT NULL | ワークフローインスタンスID |
| node_definition_id | NUMBER | FK, NOT NULL | ノード定義ID |
| node_seq | NUMBER | NOT NULL | ノード順序番号 |
| node_status | VARCHAR2(20) | NOT NULL | ノードステータス（waiting/pending/approved/rejected/skipped） |
| assigned_user_id | VARCHAR2(50) | | 割り当て承認者ID（複数承認者の場合、実際に承認した人） |
| arrived_at | TIMESTAMP | | ノード到達日時（承認可能になった日時） |
| assigned_at | TIMESTAMP | | 割り当て日時 |
| actioned_at | TIMESTAMP | | 処理日時 |
| action_comment | VARCHAR2(2000) | | 処理コメント |

**インデックス**:
- `IDX_WF_NODE_INST` (workflow_instance_id, node_seq)
- `IDX_WF_NODE_ASSIGNED` (assigned_user_id, node_status)
- `IDX_WF_NODE_STATUS_ARRIVED` (node_status, arrived_at)

**ノードステータスの説明**:
- `waiting`: 前のノードの承認待ち（まだ承認不可）
- `pending`: 承認待ち（承認可能）
- `approved`: 承認済み
- `rejected`: 却下
- `skipped`: スキップ（条件により省略）

#### T_WORKFLOW_NODE_APPROVER (ワークフローノード承認者候補)
各ノードインスタンスの承認者候補を保持。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| node_approver_id | NUMBER | PK | ノード承認者ID |
| node_instance_id | NUMBER | FK, NOT NULL | ノードインスタンスID |
| approver_user_id | VARCHAR2(50) | NOT NULL | 承認者候補のユーザーID |
| approver_order | NUMBER | | 承認者優先順位 |
| is_notified | CHAR(1) | NOT NULL | 通知済みフラグ（Y/N） |
| notified_at | TIMESTAMP | | 通知日時 |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |

**ユニーク制約**: (node_instance_id, approver_user_id)

**インデックス**:
- `IDX_NODE_APPROVER_USER` (approver_user_id)
- `IDX_NODE_APPROVER_NODE` (node_instance_id)

#### T_WORKFLOW_HISTORY (ワークフロー履歴)
承認・差戻・却下等の履歴を記録。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| history_id | NUMBER | PK | 履歴ID |
| workflow_instance_id | NUMBER | FK, NOT NULL | ワークフローインスタンスID |
| node_instance_id | NUMBER | FK, NOT NULL | ノードインスタンスID |
| action_type | VARCHAR2(20) | NOT NULL | アクション種別（approve/reject/return/skip） |
| action_user_id | VARCHAR2(50) | NOT NULL | 処理者ユーザーID |
| action_comment | VARCHAR2(2000) | | 処理コメント |
| actioned_at | TIMESTAMP | NOT NULL | 処理日時 |

**インデックス**:
- `IDX_WF_HIST_INST` (workflow_instance_id)
- `IDX_WF_HIST_USER` (action_user_id)

---

### 3. マスタテーブル

#### M_APPLICATION_TYPE (申請種類マスタ)
申請の種類を定義。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| application_type_id | NUMBER | PK | 申請種類ID |
| application_type_code | VARCHAR2(50) | NOT NULL, UNIQUE | 申請種類コード |
| application_type_name | VARCHAR2(200) | NOT NULL | 申請種類名 |
| description | VARCHAR2(1000) | | 説明 |
| workflow_definition_id | NUMBER | FK, NOT NULL | デフォルトワークフロー定義ID |
| is_multi_record | CHAR(1) | NOT NULL | 複数レコード対応フラグ（Y/N） |
| has_target_user | CHAR(1) | NOT NULL | 申請対象ユーザー有無フラグ（Y/N） |
| requires_jurisdiction | CHAR(1) | NOT NULL | 所管所属指定必須フラグ（Y/N） |
| jurisdiction_restriction | VARCHAR2(20) | | 申請可能所属制限（any/jurisdiction_only/specific） |
| allowed_shozoku_list | VARCHAR2(500) | | 申請可能所属リスト（カンマ区切り、jurisdiction_restriction='specific'時） |
| support_create | CHAR(1) | NOT NULL | 新規作成対応フラグ（Y/N） |
| support_modify | CHAR(1) | NOT NULL | 修正対応フラグ（Y/N） |
| support_delete | CHAR(1) | NOT NULL | 削除対応フラグ（Y/N） |
| resource_table_name | VARCHAR2(100) | | リソーステーブル名（既存設定格納先） |
| resource_search_query | VARCHAR2(4000) | | リソース検索SQL |
| resource_detail_query | VARCHAR2(4000) | | リソース詳細取得SQL |
| resource_validation_query | VARCHAR2(4000) | | リソース重複チェックSQL |
| resource_jurisdiction_column | VARCHAR2(100) | | リソーステーブルの所管所属カラム名 |
| is_active | CHAR(1) | NOT NULL | 有効フラグ（Y/N） |
| display_order | NUMBER | | 表示順序 |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

**補足説明**:
- `has_target_user`: Y=ユーザーに関わる申請（DBアクセス権限等）、N=ユーザーに関わらない申請（Gmailグループ等）
- `requires_jurisdiction`: Y=所管所属の指定が必須、N=所管所属は不要
- `jurisdiction_restriction`: 申請可能所属の制限
  - `any`: どの所属からでも申請可能
  - `jurisdiction_only`: リソースの所管所属からのみ申請可能
  - `specific`: 特定の所属リストからのみ申請可能
- `resource_jurisdiction_column`: リソーステーブル内の所管所属を格納するカラム名（例: owner_shozoku）

#### M_APPLICATION_FIELD (申請フィールドマスタ)
申請種類ごとの入力フィールドを定義。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| field_id | NUMBER | PK | フィールドID |
| application_type_id | NUMBER | FK, NOT NULL | 申請種類ID |
| field_code | VARCHAR2(50) | NOT NULL | フィールドコード |
| field_name | VARCHAR2(300) | NOT NULL | フィールド名 |
| field_type | VARCHAR2(20) | NOT NULL | フィールド種別（text/number/date/select/datalist/textarea/checkbox） |
| is_required_create | CHAR(1) | NOT NULL | 新規作成時必須フラグ（Y/N） |
| is_required_modify | CHAR(1) | NOT NULL | 修正時必須フラグ（Y/N） |
| is_required_delete | CHAR(1) | NOT NULL | 削除時必須フラグ（Y/N） |
| is_editable_modify | CHAR(1) | NOT NULL | 修正時編集可能フラグ（Y/N） |
| is_multi_row | CHAR(1) | NOT NULL | 複数行対応フラグ（Y/N） |
| validation_rule_id | NUMBER | FK | バリデーションルールID |
| pulldown_group_id | NUMBER | FK | プルダウングループID |
| resource_column_name | VARCHAR2(100) | | リソーステーブルのカラム名（既存データからの値設定用） |
| display_order | NUMBER | | 表示順序 |
| default_value | VARCHAR2(200) | | デフォルト値 |
| placeholder | VARCHAR2(200) | | プレースホルダー |
| help_text | VARCHAR2(500) | | ヘルプテキスト |

**ユニーク制約**: (application_type_id, field_code)

#### M_VALIDATION_RULE (バリデーションルールマスタ)
フィールドのバリデーションルールを定義。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| validation_rule_id | NUMBER | PK | バリデーションルールID |
| rule_name | VARCHAR2(100) | NOT NULL | ルール名 |
| rule_type | VARCHAR2(20) | NOT NULL | ルール種別（regex/length/range/custom） |
| rule_expression | VARCHAR2(1000) | | ルール式（正規表現等） |
| min_value | NUMBER | | 最小値 |
| max_value | NUMBER | | 最大値 |
| min_length | NUMBER | | 最小文字数 |
| max_length | NUMBER | | 最大文字数 |
| custom_function | VARCHAR2(200) | | カスタム関数名 |
| error_message | VARCHAR2(500) | NOT NULL | エラーメッセージ |

#### M_PULLDOWN_GROUP (プルダウングループマスタ)
プルダウンの選択肢グループを定義。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| pulldown_group_id | NUMBER | PK | プルダウングループID |
| group_code | VARCHAR2(50) | NOT NULL, UNIQUE | グループコード |
| group_name | VARCHAR2(200) | NOT NULL | グループ名 |
| description | VARCHAR2(500) | | 説明 |
| is_dynamic | CHAR(1) | NOT NULL | 動的取得フラグ（Y/N） |
| dynamic_query | VARCHAR2(2000) | | 動的取得SQL |

#### M_PULLDOWN_OPTION (プルダウン選択肢マスタ)
プルダウンの個別選択肢を定義。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| option_id | NUMBER | PK | 選択肢ID |
| pulldown_group_id | NUMBER | FK, NOT NULL | プルダウングループID |
| option_value | VARCHAR2(200) | NOT NULL | 選択肢値 |
| option_label | VARCHAR2(200) | NOT NULL | 選択肢ラベル |
| display_order | NUMBER | | 表示順序 |
| is_active | CHAR(1) | NOT NULL | 有効フラグ（Y/N） |
| parent_option_id | NUMBER | FK | 親選択肢ID（階層構造用） |

---

### 4. ワークフロー定義テーブル

#### M_WORKFLOW_DEFINITION (ワークフロー定義マスタ)
ワークフロー全体の定義。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| workflow_definition_id | NUMBER | PK | ワークフロー定義ID |
| workflow_name | VARCHAR2(200) | NOT NULL | ワークフロー名 |
| workflow_code | VARCHAR2(50) | NOT NULL, UNIQUE | ワークフローコード |
| description | VARCHAR2(1000) | | 説明 |
| is_active | CHAR(1) | NOT NULL | 有効フラグ（Y/N） |
| version | NUMBER | NOT NULL | バージョン |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

#### M_WORKFLOW_NODE_DEFINITION (ワークフローノード定義マスタ)
ワークフローの各承認ノードを定義。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| node_definition_id | NUMBER | PK | ノード定義ID |
| workflow_definition_id | NUMBER | FK, NOT NULL | ワークフロー定義ID |
| node_seq | NUMBER | NOT NULL | ノード順序番号 |
| node_name | VARCHAR2(200) | NOT NULL | ノード名 |
| node_type | VARCHAR2(50) | NOT NULL | ノード種別（applicant_dept/target_dept/jurisdiction_dept/specific_dept/final/report） |
| specific_shozoku | VARCHAR2(20) | | 特定所属コード（specific_dept時） |
| is_required | CHAR(1) | NOT NULL | 必須フラグ（Y/N） |
| skip_condition | VARCHAR2(500) | | スキップ条件（SQL式） |
| is_report_only | CHAR(1) | NOT NULL | 報告のみフラグ（Y/N） |
| approver_selection_required | CHAR(1) | NOT NULL | 承認者選択必須フラグ（Y/N） |

**ユニーク制約**: (workflow_definition_id, node_seq)

**ノード種別の説明**:
- `applicant_dept`: 申請者の所属長承認
- `target_dept`: 申請対象ユーザーの所属長承認（has_target_user='Y'の場合のみ）
- `jurisdiction_dept`: 申請対象リソースの所管所属長承認
  - スキップ条件例: `applicant_shozoku = jurisdiction_shozoku`（申請者の所属と所管が同じ場合は省略）
- `specific_dept`: 特定所属の承認（経営企画部長、法務コンプライアンス部長等）
- `final`: 最終承認（システム企画室、システム開発部長等）
- `report`: 報告（最終承認後の報告、処理完了を待たない）

#### M_NODE_APPROVER (ノード承認者マスタ)
ノードごとの承認者候補を定義（特定所属の場合）。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| node_approver_id | NUMBER | PK | ノード承認者ID |
| node_definition_id | NUMBER | FK, NOT NULL | ノード定義ID |
| approver_user_id | VARCHAR2(50) | NOT NULL | 承認者ユーザーID |
| approver_order | NUMBER | | 承認者優先順位 |
| is_active | CHAR(1) | NOT NULL | 有効フラグ（Y/N） |

---

### 5. リソーステーブル（既存設定保持）

#### T_RESOURCE_GMAIL_GROUP (Gmailグループリソース)
Gmailグループの既存設定を保持するテーブル（例）。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| resource_id | VARCHAR2(200) | PK | リソースID（グループメールアドレス） |
| group_name | VARCHAR2(200) | NOT NULL | グループ名 |
| group_email | VARCHAR2(200) | NOT NULL, UNIQUE | グループメールアドレス |
| description | VARCHAR2(1000) | | 説明 |
| owner_shozoku | VARCHAR2(20) | | 所管所属コード |
| member_count | NUMBER | | メンバー数 |
| created_date | DATE | | 作成日 |
| last_updated | TIMESTAMP | NOT NULL | 最終更新日時 |
| is_active | CHAR(1) | NOT NULL | 有効フラグ（Y/N） |
| sync_source | VARCHAR2(50) | | 同期元（google_api等） |

**インデックス**:
- `IDX_GMAIL_GROUP_EMAIL` (group_email)
- `IDX_GMAIL_GROUP_OWNER` (owner_shozoku)

**注記**: 
- このテーブルは日次バッチ処理でGoogle Workspace APIから取得したデータを格納
- 申請種類ごとに対応するリソーステーブルを作成（命名規則: T_RESOURCE_*）

#### T_RESOURCE_SYNC_LOG (リソース同期ログ)
リソーステーブルへの同期処理ログ。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| sync_log_id | NUMBER | PK | 同期ログID |
| resource_table_name | VARCHAR2(100) | NOT NULL | リソーステーブル名 |
| sync_start_time | TIMESTAMP | NOT NULL | 同期開始日時 |
| sync_end_time | TIMESTAMP | | 同期終了日時 |
| sync_status | VARCHAR2(20) | NOT NULL | 同期ステータス（success/failed/partial） |
| records_processed | NUMBER | | 処理レコード数 |
| records_inserted | NUMBER | | 挿入レコード数 |
| records_updated | NUMBER | | 更新レコード数 |
| records_deleted | NUMBER | | 削除レコード数 |
| error_message | CLOB | | エラーメッセージ |
| executed_by | VARCHAR2(50) | | 実行者 |

**インデックス**:
- `IDX_SYNC_LOG_TABLE` (resource_table_name, sync_start_time)

---

### 6. シーケンス

```sql
CREATE SEQUENCE SEQ_APPLICATION_ID START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE SEQ_DETAIL_ID START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE SEQ_WORKFLOW_INSTANCE_ID START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE SEQ_NODE_INSTANCE_ID START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE SEQ_NODE_APPROVER_ID START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE SEQ_HISTORY_ID START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE SEQ_SYNC_LOG_ID START WITH 1 INCREMENT BY 1;
```

---

### 7. 既存参照テーブル（READ ONLY）

#### nam_user_admin.e_imdb2_users
ユーザー情報を取得する既存テーブル。

主要カラム（推定）:
- user_id: ユーザーID
- user_name: ユーザー名
- shozoku: 所属コード（本務）
- shozoku_fukumu: 兼務所属コード

#### nam_ope.e_approver
承認者情報を取得する既存テーブル。

主要カラム（推定）:
- shozoku: 所属コード
- approver_user_id: 承認者ユーザーID
- approver_name: 承認者名

---

## ER図（概念図）

```
[M_APPLICATION_TYPE] 1---N [T_APPLICATION] 1---N [T_APPLICATION_DETAIL] N---1 [M_APPLICATION_FIELD]
                     |                     |
                     |                     1
                     |                     |
                     1                     N
                     |                 [T_WORKFLOW_INSTANCE] 1---N [T_WORKFLOW_NODE_INSTANCE]
                     |                                        |
                     N                                        1
                     |                                        |
              [M_WORKFLOW_DEFINITION] 1---N [M_WORKFLOW_NODE_DEFINITION] 1---N [M_NODE_APPROVER]
```

---

## データ投入順序

1. マスタデータ（M_で始まるテーブル）
   - M_WORKFLOW_DEFINITION
   - M_WORKFLOW_NODE_DEFINITION
   - M_NODE_APPROVER
   - M_APPLICATION_TYPE
   - M_APPLICATION_FIELD
   - M_VALIDATION_RULE
   - M_PULLDOWN_GROUP
   - M_PULLDOWN_OPTION

2. トランザクションデータ（T_で始まるテーブル）
   - T_APPLICATION
   - T_APPLICATION_DETAIL
   - T_WORKFLOW_INSTANCE
   - T_WORKFLOW_NODE_INSTANCE
   - T_WORKFLOW_HISTORY
