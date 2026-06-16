# ワークフロー設定ガイド（申請タイプ登録・修正）

このガイドでは、新しい申請タイプとワークフローを登録・修正する手順を説明します。

---

## 1. 設定の全体フロー（5ステップ）

ワークフローを新規作成する場合、以下の順序で設定を行います。

### ステップ1: 申請タイプ作成（M_APPLICATION_TYPE）

申請の基本情報を定義します。**管理画面から登録・編集可能です。**

**必須項目:**
- `application_type_code` - 一意の識別コード（例: `ACC001`, `DB_ACCESS`）
- `application_type_name` - 表示名（例: `アカウント管理`）
- `is_multi_record` - 単一レコード（`'N'`）か複数レコード（`'Y'`）か
- `workflow_definition_id` - 適用するワークフロー定義ID

**操作タイプの設定:**
- `support_create` - 新規作成申請を許可（`'Y'/'N'`）
- `support_modify` - 修正申請を許可（`'Y'/'N'`）
- `support_delete` - 削除申請を許可（`'Y'/'N'`）

**リソース検索の設定（修正・削除時に必要）:**
- `resource_search_query` - 既存リソース検索SQL（`:search_keyword`, `:applicant_user_id`, `:applicant_shozoku`パラメータ使用可）
- `resource_detail_query` - リソース詳細取得SQL（`:resource_id`パラメータ使用）
- `resource_jurisdiction_column` - 所管所属を取得するカラム名（例: `owner_shozoku`）

**複数レコード申請の設定:**
- `record_add_mode` - `'select'`（既存から選択）または `'free'`（自由入力）
- `resource_member_query` - 既存メンバーと追加候補を取得するSQL
  - **必須カラム**: `is_member`（`'Y'`=既存メンバー, `'N'`=追加候補）
  - **推奨カラム**: `is_updatable`（`'Y'`=編集可, `'N'`=編集不可、既存レコード修正時にほぼ必須）

**所属制限の設定:**
- `jurisdiction_restriction` - `'any'`（制限なし）または `'specific'`（特定所属のみ）
- `allowed_shozoku_list` - 申請可能所属のカンマ区切りリスト（`'specific'`の場合のみ）

**詳細**: [APPLICATION_TYPE_FIELDS.md](APPLICATION_TYPE_FIELDS.md)

---

### ステップ2: フィールド定義（M_APPLICATION_FIELD）

申請画面で入力するフィールドを定義します。**管理画面から登録・編集可能です。**

**必須項目:**
- `application_type_id` - 申請タイプID **（管理画面では自動設定）**
- `field_code` - フィールド識別子（例: `mailaddress`, `groupname`）
- `field_name` - 表示名（例: `メールアドレス`）
- `field_type` - 入力タイプ（`text`, `textarea`, `select`, `datalist`, `date`, `checkbox`）
- `display_order` - 表示順序
- `is_required` - 必須フラグ（`'Y'/'N'`）

**フィールドタイプ別の追加設定:**

| field_type | 必要な設定 | 説明 |
|-----------|-----------|------|
| `select` | `field_options_query` | プルダウン選択肢を取得するSQL |
| `datalist` | `field_options_query` | 入力候補を取得するSQL |
| `text`, `textarea` | `validation_rule` | バリデーションルール（任意） |

**validation_rule の設定例:**
```python
# 必須チェック
required

# 正規表現チェック
regex:^[a-zA-Z0-9_]+$

# 複数条件
required|regex:^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
```

**詳細**: [VALIDATION_RULES.md](VALIDATION_RULES.md), [FIELD_TYPE_DATALIST.md](FIELD_TYPE_DATALIST.md)

---

### ステップ3: ワークフロー定義作成（M_WORKFLOW_DEFINITION）

ワークフロー全体を定義します（複数の申請タイプで共有可能）。**管理画面から登録・編集可能です。**

**必須項目:**
- `workflow_name` - ワークフロー名（例: `システムアクセス申請フロー`）
- `description` - 説明（例: `標準的な3段階承認`）
- `is_active` - 有効フラグ（`'Y'/'N'`）

---

### ステップ4: ワークフローノード定義（M_WORKFLOW_NODE_DEFINITION）

承認ノードを順番に定義します。**管理画面から登録・編集可能です。**

**必須項目:**
- `workflow_definition_id` - ワークフロー定義ID **（管理画面では自動設定）**
- `node_seq` - ノード順序（1, 2, 3...）
- `node_name` - ノード表示名（例: `申請者所属長承認`）
- `node_type` - ノードタイプ（下記参照）
- `specific_value` - ノードタイプ別の追加設定値（`specific_node`, `specific_dept`, `resource_dept`で使用）
- `is_required` - 必須フラグ（`'Y'/'N'`）
- `approver_selection_required` - 承認者選択フラグ（`'Y'/'N'`）

**ノードタイプの選択:**

「3. ワークフローノード選択ガイド」を参照してください。

**スキップ条件の設定（任意）:**
- `skip_condition` - Python式でスキップ条件を記述（例: `fields.get('mailaddress', '').endswith('@nam.co.jp')`）

**詳細**: [WORKFLOW_NODE_TYPES.md](WORKFLOW_NODE_TYPES.md), [SKIP_CONDITION_EXAMPLES.md](SKIP_CONDITION_EXAMPLES.md)

---

### ステップ5: 承認者定義（M_NODE_APPROVER）

`specific_node`タイプのノードで使用する固定承認者を定義します。**管理画面から登録・編集可能です。**

**必須項目:**
- `specific_node` - ノード識別子（ステップ4の`specific_value`と一致させる）
- `approver_user_id` - 承認者のユーザーID
- `approver_order` - 承認者の表示順序

**注意:**
- `applicant_dept`, `jurisdiction_dept`, `specific_dept`, `resource_dept`, `multiple_dept`は承認者を動的に取得するため、このテーブルへの登録は不要です。
- `specific_node`タイプを使用する場合のみ、このステップが必要です。

---

## 2. 申請タイプ設定の決定事項チェックリスト

新しい申請タイプを作成する前に、以下の項目を決定してください。

### 基本設計

- [ ] **申請の対象は何か？**（例: アカウント、データベース、グループメンバー）
- [ ] **単一レコードか複数レコードか？**
  - 単一: 1回の申請で1件のみ操作（例: アカウント作成）
  - 複数: 1回の申請で複数件を操作（例: メンバー一括追加）
- [ ] **どの操作をサポートするか？**
  - [ ] 新規作成（create）
  - [ ] 修正（modify）
  - [ ] 削除（delete）

### リソース検索（修正・削除をサポートする場合）

- [ ] **既存リソースをどう検索するか？**
  - 検索対象テーブル/ビュー名
  - 検索条件（キーワード、申請者所属、申請者自身のリソースのみ等）
  - 表示するカラム（ID、名前、説明等）
- [ ] **所管所属はどのカラムに格納されているか？**
  - カラム名（例: `owner_shozoku`, `jurisdiction_dept_cd`）

### 複数レコード申請の場合

- [ ] **レコード追加モードは？**
  - `'select'`: 既存レコード（is_member='N'）から選択して追加
  - `'free'`: 空のフォームを追加して自由入力
- [ ] **既存メンバーをどう取得するか？**
  - 取得SQL
  - **必須カラム**: `is_member`（`'Y'`=既存メンバー, `'N'`=追加候補）
  - **推奨カラム**: `is_updatable`（`'Y'`=編集可, `'N'`=編集不可）
    - 既存レコードを修正する場合、`is_updatable`カラムはほぼ必須です
    - 編集不可のレコードは表示のみで、変更できないように制御されます

### ワークフロー設計

- [ ] **どの承認ノードが必要か？**
  - [ ] 申請者所属長承認（`applicant_dept`）
  - [ ] 所管所属長承認（`jurisdiction_dept`）
  - [ ] 対象ユーザー所属長承認（`jurisdiction_dept`でリソースにユーザーを設定）
  - [ ] 変更対象所属長承認（`multiple_dept`、複数レコード専用）
  - [ ] 特定部署承認（`specific_dept`、例: 法務部）
  - [ ] 固定メンバー承認（`specific_node`、例: システム企画室）
  - [ ] リソース所管承認（`resource_dept`、例: Boxフォルダ）
  - [ ] 最終承認（`final`）
  - [ ] 報告（`report`）
- [ ] **スキップ条件が必要なノードはあるか？**
  - 条件式（Python式）

### 所属制限

- [ ] **申請可能な所属を制限するか？**
  - 制限なし（`'any'`）
  - 特定所属のみ（`'specific'` + `allowed_shozoku_list`）

### 入力フィールド

- [ ] **申請画面で入力するフィールドは何か？**
  - フィールドコード、表示名、入力タイプ、必須/任意
  - プルダウンの選択肢取得SQL（`select`/`datalist`の場合）
  - バリデーションルール（`text`/`textarea`の場合）

---

## 3. ワークフローノード選択ガイド

申請の承認フローに応じて、適切なノードタイプを選択してください。

### 所属長承認系

| node_type | 承認者 | 用途 | specific_value |
|-----------|--------|------|----------------|
| **applicant_dept** | **申請者の所属長** | ほぼすべての申請で必要 | 不要 |
| **jurisdiction_dept** | **所管所属長**<br>※リソースがユーザーの場合は対象ユーザー所属長 | リソースに所管所属がある場合<br>（データベース、システム、ユーザー等） | 不要 |
| **multiple_dept** | **変更対象所属長**<br>（複数レコード申請専用） | メンバーの所属変更申請等 | 不要 |

**注意:**
- `applicant_dept`は常に実行されます
- `jurisdiction_dept`は`applicant_shozoku == jurisdiction_shozoku`の場合、自動スキップされます
- `multiple_dept`は並列承認（各所属から最低1人承認が必要）となります

### 特定承認者系

| node_type | 承認者 | 用途 | specific_value |
|-----------|--------|------|----------------|
| **specific_node** | **固定メンバー**<br>（M_NODE_APPROVERで定義） | システム企画室、DBA、情報セキュリティ委員会等 | 識別子（例: `'sys_planning'`） |
| **specific_dept** | **特定部署の承認者**<br>（e_approverから取得） | 法務部、経営企画部等 | 部署コード（例: `'2310000'`） |
| **resource_dept** | **リソース×所属で動的決定**<br>（指定テーブルから取得） | Boxフォルダアクセス権限等 | テーブル名（例: `'nam_user_admin.boxex_approver'`） |

**使い分け:**
- **固定メンバー**を承認者にする → `specific_node`
- **特定部署の承認者**（組織マスタで管理）→ `specific_dept`
- **リソースと申請者所属で承認者が変わる** → `resource_dept`

### 最終承認・報告

| node_type | 用途 | specific_value |
|-----------|------|----------------|
| **final** | 最終承認（通常はシステム企画室） | 任意（M_NODE_APPROVERで定義可） |
| **report** | 報告のみ（承認不要） | 任意 |

---

## 4. トラブルシューティング

### Q1: 承認者が表示されない

**原因:**
- 承認者テーブル（`e_approver`, `M_NODE_APPROVER`）にデータが登録されていない
- `resource_dept`の場合、`specific_value`で指定したテーブルにデータがない

**確認方法:**
```sql
-- applicant_dept / jurisdiction_dept / specific_dept の場合
SELECT * FROM nam_ope.e_approver WHERE department_cd = '1234567';

-- specific_node の場合
SELECT * FROM M_NODE_APPROVER WHERE specific_node = 'sys_planning';

-- resource_dept の場合
SELECT * FROM nam_user_admin.boxex_approver 
WHERE resource_id = 'xxxxx' AND shozoku = '1234567';
```

---

### Q2: スキップ条件が効かない

**原因:**
- `skip_condition`の式にエラーがある（ログに記録されます）
- フィールドコードが間違っている
- 変数名が間違っている（`application`, `resource`, `fields`のみ使用可能）

**確認方法:**
```sql
-- フィールドコードの確認
SELECT field_code, field_name 
FROM M_APPLICATION_FIELD 
WHERE application_type_id = (
    SELECT application_type_id FROM M_APPLICATION_TYPE WHERE application_type_code = 'DB_ACCESS'
);

-- スキップ条件の確認
SELECT node_name, skip_condition 
FROM M_WORKFLOW_NODE_DEFINITION 
WHERE workflow_definition_id = 1;
```

**ログ確認:**
```powershell
Get-Content C:\inetpub\wwwroot\genWF\logs\app.log -Tail 50 | Select-String "skip"
```

---

### Q3: jurisdiction_shozoku（所管所属）が設定されない

**原因:**
- `resource_jurisdiction_column`が設定されていない
- `resource_detail_query`の実行結果に指定したカラムが存在しない

**確認方法:**
```sql
-- resource_jurisdiction_column の確認
SELECT resource_jurisdiction_column, resource_detail_query 
FROM M_APPLICATION_TYPE 
WHERE application_type_code = 'DB_ACCESS';

-- resource_detail_query の実行結果確認（:resource_idを実際の値に置き換え）
SELECT * FROM your_table WHERE resource_id = 'actual_id';
```

---

### Q4: 複数レコード申請でメンバーが表示されない

**原因:**
- `resource_member_query`が設定されていない
- `is_member`カラムが結果に含まれていない
- SQLにエラーがある

**確認方法:**
```sql
-- resource_member_query の確認
SELECT resource_member_query 
FROM M_APPLICATION_TYPE 
WHERE application_type_code = 'MEMBER_MGMT';

-- 実行結果確認（:resource_idを実際の値に置き換え）
-- ※is_member カラムが 'Y' または 'N' で返されることを確認
SELECT * FROM (
    -- ここに resource_member_query の内容をペースト
) WHERE ROWNUM <= 10;
```

---

### Q5: resource_dept の承認者が取得できない

**原因:**
- `specific_value`で指定したテーブルが存在しない
- テーブルに`resource_id`, `shozoku`, `approver`カラムが存在しない
- 該当するデータがテーブルに登録されていない

**必須テーブル構造:**
```sql
CREATE TABLE your_schema.your_table (
    resource_id VARCHAR2(200),  -- 必須
    shozoku VARCHAR2(20),       -- 必須
    approver VARCHAR2(50),      -- 必須
    -- その他の任意カラム
);
```

**確認方法:**
```sql
-- テーブル構造の確認
DESC nam_user_admin.boxex_approver;

-- データの確認
SELECT * FROM nam_user_admin.boxex_approver 
WHERE resource_id = 'actual_resource_id' 
  AND shozoku = 'actual_shozoku';
```

---

## 5. 詳細ドキュメントへのリンク

各項目の詳細仕様は以下のドキュメントを参照してください。

### 設定作業者向け

- [APPLICATION_TYPE_FIELDS.md](APPLICATION_TYPE_FIELDS.md) - 申請タイプ全フィールド仕様
- [WORKFLOW_NODE_TYPES.md](WORKFLOW_NODE_TYPES.md) - ワークフローノード全タイプ仕様
- [SKIP_CONDITION_EXAMPLES.md](SKIP_CONDITION_EXAMPLES.md) - スキップ条件サンプル集
- [VALIDATION_RULES.md](VALIDATION_RULES.md) - バリデーションルール一覧
- [FIELD_TYPE_DATALIST.md](FIELD_TYPE_DATALIST.md) - datalist フィールドタイプの使い方
- [MULTI_RECORD_ADD_MODES.md](MULTI_RECORD_ADD_MODES.md) - 複数レコード申請のレコード追加モード
- [UNIQUE_KEY_CONSTRAINT.md](UNIQUE_KEY_CONSTRAINT.md) - 一意キー制約の設定方法
- [JSON_IMPORT_SPECIFICATION.md](JSON_IMPORT_SPECIFICATION.md) - JSON インポート/エクスポート仕様

### 開発者向け

- [database_design.md](database_design.md) - データベース設計
- [system_architecture.md](system_architecture.md) - システムアーキテクチャ
- [APP_MODULES.md](APP_MODULES.md) - アプリケーションモジュール構成
- [application_structure.md](application_structure.md) - アプリケーション構造


---
