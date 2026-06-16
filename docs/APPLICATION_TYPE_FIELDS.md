# 申請タイプの設定項目

申請タイプ（`M_APPLICATION_TYPE`）の各フィールドの説明と用途。

---

## 基本情報

### application_type_code
- **型**: VARCHAR2(50)
- **必須**: はい
- **説明**: 一意の識別コード（例: `ACC001`, `DB_ACCESS`）
- **備考**: 作成後は変更不可

### application_type_name
- **型**: VARCHAR2(200)
- **必須**: はい
- **説明**: 表示用の名前（例: `アカウント管理`, `データベースアクセス権限申請`）

### description
- **型**: VARCHAR2(1000)
- **必須**: いいえ
- **説明**: 申請タイプの説明文

### is_under_development
- **型**: CHAR(1) `'Y'/'N'`
- **デフォルト**: `'N'`
- **説明**: 開発中フラグ
- **動作**:
  - `'Y'`: 管理者のみ表示、一般ユーザーは申請提出不可
  - `'N'`: すべてのユーザーが利用可能

---

## 対応する操作（アクションタイプ）

### is_multi_record
- **型**: CHAR(1) `'Y'/'N'`
- **デフォルト**: `'N'`
- **説明**: 複数レコード入力フラグ
- **動作**:
  - `'N'`: 単一レコード申請（create/modify/delete を個別に申請）
  - `'Y'`: 複数レコード申請（1回の申請で複数の追加・修正・削除を行う）

### record_add_mode
- **型**: VARCHAR2(20) `'select'/'free'`
- **デフォルト**: `'select'`
- **説明**: レコード追加モード（`is_multi_record='Y'` の場合のみ有効）
- **動作**:
  - `'select'`: `is_member='N'` のレコードから選択して追加（例: メンバー管理）
  - `'free'`: 空のフォームを追加して自由に入力（例: 経費明細）
- **詳細**: [MULTI_RECORD_ADD_MODES.md](MULTI_RECORD_ADD_MODES.md)

### support_create / support_modify / support_delete
- **型**: CHAR(1) `'Y'/'N'`
- **デフォルト**: `'Y'/'N'/'N'`
- **説明**: 各アクションタイプのサポート有無（単一レコード申請時に有効）
- **動作**:
  - チェックされたアクションのみ申請画面に表示される
  - `support_create='Y'`: 新規作成申請が可能
  - `support_modify='Y'`: 修正申請が可能
  - `support_delete='Y'`: 削除申請が可能

---

## 申請対象設定

### has_target_user
- **型**: CHAR(1) `'Y'/'N'`
- **デフォルト**: `'N'`
- **説明**: 申請対象ユーザー有無フラグ
- **現状**: **未実装**（将来拡張用）
- **想定用途**: 
  - `'Y'`: 申請対象となるユーザーを指定する申請（例: 他のユーザーのアカウント作成）
  - `'N'`: 申請者自身に対する申請

### requires_jurisdiction
- **型**: CHAR(1) `'Y'/'N'`
- **デフォルト**: `'N'`
- **説明**: 所管所属指定必須フラグ
- **現状**: **未実装**（将来拡張用）
- **想定用途**:
  - `'Y'`: リソースの所管所属を必ず指定する必要がある
  - `'N'`: 所管所属の指定は任意

### jurisdiction_restriction
- **型**: VARCHAR2(20) `'any'/'specific'`
- **デフォルト**: `'any'`
- **説明**: 申請可能所属制限
- **動作**:
  - `'any'`: すべての所属から申請可能
  - `'specific'`: `allowed_shozoku_list` で指定した所属のみ申請可能
- **実装箇所**: `app/models/application_type.py` の `can_user_apply()`
- **注意**: 所管所属による制限は `resource_search_query` で `:applicant_shozoku` パラメータを使用して実現します
  ```sql
  -- 例: 申請者の所属がowner_shozokuと一致するリソースのみ表示
  SELECT 
    resource_id,
    resource_name,
    owner_shozoku
  FROM resources
  WHERE owner_shozoku = :applicant_shozoku
  ```

### allowed_shozoku_list
- **型**: VARCHAR2(500)
- **説明**: 申請可能所属リスト（カンマ区切り）
- **例**: `'1234567,2345678,3456789'`
- **動作**: `jurisdiction_restriction='specific'` の場合のみ有効
- **実装箇所**: `app/models/application_type.py` の `can_user_apply()`

---

## ワークフロー設定

### workflow_definition_id
- **型**: NUMBER
- **必須**: はい
- **説明**: 適用するワークフロー定義のID
- **備考**: `M_WORKFLOW_DEFINITION` テーブルを参照

---

## リソース設定（修正・削除時の既存データ参照）

### resource_search_query
- **型**: VARCHAR2(4000)
- **説明**: 親リソース検索クエリ
- **用途**: 修正・削除時に既存リソースを検索するためのSQL
- **パラメータ**:
  - `:search_keyword` - 検索キーワード
  - `:applicant_user_id` - 申請者のユーザーCD
  - `:applicant_shozoku` - 申請者所属
- **要件**:
  - 第1カラムは `resource_id` としてエイリアス指定が必須
  - 例: `SELECT user_cd AS resource_id, user_name FROM users WHERE user_name LIKE '%' || :search_keyword || '%'`
  - 申請者の所属で制限する場合: `WHERE owner_shozoku = :applicant_shozoku`
  - 申請者本人のリソースのみに制限する場合: `WHERE owner_user_id = :applicant_user_id`

### resource_detail_query
- **型**: VARCHAR2(4000)
- **説明**: 親リソース詳細クエリ
- **用途**: 選択されたリソースの詳細を取得するSQL
- **パラメータ**:
  - `:resource_id` - 親リソースID
- **例**: `SELECT * FROM users WHERE user_cd = :resource_id`

### resource_member_query
- **型**: CLOB
- **説明**: 子レコード一覧クエリ（複数レコード申請時に使用）
- **用途**: 既存レコードと追加候補を取得するSQL
- **パラメータ**:
  - `:resource_id` - 親リソースID
  - `:applicant_user_id` - 申請者のユーザーCD
  - `:applicant_shozoku` - 申請者所属
- **要件**:
  - `is_member` カラムが必須（`'Y'`=既存メンバー, `'N'`=追加候補）
  - `is_updatable` カラムを含めると編集可否を制御可能
- **例**:
  ```sql
  SELECT
    user_id,
    user_name,
    email,
    CASE
      WHEN EXISTS (
        SELECT 1 FROM gmail_group_members
        WHERE group_id = :resource_id AND user_id = t.user_id
      ) THEN 'Y'
      ELSE 'N'
    END AS is_member,
    'Y' AS is_updatable
  FROM users t
  WHERE user_status = 'active'
    AND user_id != :applicant_user_id  -- 申請者自身を除外する例
  ORDER BY is_member DESC, user_name
  ```

### resource_validation_query
- **型**: VARCHAR2(4000)
- **説明**: リソースバリデーションクエリ
- **現状**: **未実装**（将来拡張用）
- **想定用途**: 申請前にリソースの状態をチェックするSQL

### resource_jurisdiction_column
- **型**: VARCHAR2(100)
- **説明**: 所管所属を取得するカラム名
- **用途**: `resource_detail_query` の結果から所管所属を取得するカラム名を指定
- **例**: `owner_shozoku`, `jurisdiction_dept_cd`
- **動作**:
  - `resource_detail_query` の実行結果から `resource_jurisdiction_column` で指定したカラムの値を取得
  - `application.jurisdiction_shozoku` に格納される
  - ワークフローの `skip_condition` で `application.get('jurisdiction_shozoku')` として参照可能

---

## 管理設定

### is_active
- **型**: CHAR(1) `'Y'/'N'`
- **デフォルト**: `'Y'`
- **説明**: 有効フラグ
- **動作**:
  - `'Y'`: 有効（申請可能）
  - `'N'`: 無効（非表示）

### display_order
- **型**: NUMBER
- **説明**: 表示順序
- **備考**: 申請タイプ一覧での表示順を制御

### created_at / updated_at
- **型**: TIMESTAMP
- **説明**: 作成日時 / 更新日時
- **備考**: 自動設定

---

## 申請フロー別の設定例

### 1. 単一レコード新規申請（アカウント作成）

```sql
is_multi_record = 'N'
support_create = 'Y'
support_modify = 'N'
support_delete = 'N'
jurisdiction_restriction = 'any'
```

### 2. 単一レコード修正・削除（アカウント管理）

```sql
is_multi_record = 'N'
support_create = 'N'
support_modify = 'Y'
support_delete = 'Y'
resource_search_query = 'SELECT user_cd AS resource_id, user_name FROM users WHERE ...'
resource_detail_query = 'SELECT * FROM users WHERE user_cd = :resource_id'
```

### 3. 複数レコード（メンバー管理）- 候補選択モード

```sql
is_multi_record = 'Y'
record_add_mode = 'select'
resource_member_query = 'SELECT ..., CASE WHEN EXISTS(...) THEN ''Y'' ELSE ''N'' END AS is_member FROM ...'
```

### 4. 複数レコード（経費明細）- 自由入力モード

```sql
is_multi_record = 'Y'
record_add_mode = 'free'
resource_member_query = NULL  -- または既存明細取得用クエリ
```

### 5. 所管所属制限あり（resource_search_queryで実現）

```sql
jurisdiction_restriction = 'any'
resource_search_query = 'SELECT resource_id, resource_name FROM resources WHERE owner_shozoku = :applicant_shozoku'
resource_detail_query = 'SELECT * FROM resources WHERE resource_id = :resource_id'
resource_jurisdiction_column = 'owner_shozoku'
```

**ポイント**: `resource_search_query` で `:applicant_shozoku` を条件に入れることで、申請者の所属が所管する（owner_shozoku が一致する）リソースのみ検索結果に表示されます。

### 6. 特定所属のみ申請可能

```sql
jurisdiction_restriction = 'specific'
allowed_shozoku_list = '1234567,2345678,3456789'
```

---

## 未実装フィールド（将来拡張用）

以下のフィールドはDBスキーマに存在しますが、現在のロジックでは使用されていません。

### has_target_user
- 他のユーザーのアカウントを申請する機能を実装する際に使用予定

### requires_jurisdiction
- 所管所属の指定を必須にする機能を実装する際に使用予定

### resource_validation_query
- 申請前にリソースの状態をチェックする機能を実装する際に使用予定

---

## 関連ドキュメント

- [MULTI_RECORD_ADD_MODES.md](MULTI_RECORD_ADD_MODES.md) - 複数レコード申請のレコード追加モード
- [WORKFLOW_NODE_TYPES.md](WORKFLOW_NODE_TYPES.md) - ワークフローノードタイプ
- [SKIP_CONDITION_EXAMPLES.md](SKIP_CONDITION_EXAMPLES.md) - ワークフローのスキップ条件
