# ワークフローノードタイプ一覧

ワークフローノード定義（`M_WORKFLOW_NODE_DEFINITION`）で使用可能な`node_type`の説明です。

## ノードタイプ一覧

| node_type | 名称 | 説明 | specific_value | 承認者の取得元 |
|-----------|------|------|----------------|----------------|
| `applicant_dept` | 申請者所属長承認 | 申請者の所属長が承認 | 不要 | `application.applicant_shozoku` → `e_approver` |
| `jurisdiction_dept` | 所管所属長承認 | 所管所属の所属長が承認<br>※リソースがユーザーの場合は対象ユーザー所属長承認 | 不要 | `application.jurisdiction_shozoku` → `e_approver` |
| `specific_node` | 特定ノード承認 | 事前定義された承認者が承認 | 必須（識別子） | `M_NODE_APPROVER` テーブル |
| `specific_dept` | 特定部署承認 | 指定した部署の承認者が承認 | 必須（部署コード） | `e_approver` (department_cd一致) |
| `resource_dept` | リソース所管承認 | リソースIDと申請者所属から承認者を取得 | 必須（テーブル名） | specific_valueで指定したテーブル/View |
| `multiple_dept` | 複数所属長承認 | 変更される所属の所属長が承認（複数レコード申請用） | 不要 | `T_APPLICATION_DETAIL` (field_code='shozoku') → `e_approver` |
| `report` | 報告 | 報告のみ（承認不要） | 任意 | `M_NODE_APPROVER` または既定 |

## 各ノードタイプの詳細

### 1. applicant_dept（申請者所属長承認）

申請者が所属する部署の承認者が承認を行います。

**設定例：**
```sql
INSERT INTO M_WORKFLOW_NODE_DEFINITION (
    node_definition_id, workflow_definition_id, node_seq,
    node_name, node_type, specific_value,
    is_required, approver_selection_required
) VALUES (
    SEQ_WORKFLOW_NODE_DEF.NEXTVAL, 1, 1,
    '申請者所属長承認', 'applicant_dept', NULL,
    'Y', 'Y'  -- 承認者選択が必要
);
```

**承認者取得ロジック：**
1. `application.applicant_shozoku`（申請者所属コード）を取得
2. `e_approver`テーブルから`department_cd`が一致するレコードを検索
3. `user_cd`を承認者として登録

**スキップ条件：**
- なし（常に実行）

---

### 2. jurisdiction_dept（所管所属長承認）

申請対象リソースを所管する部署の承認者が承認を行います。

**使用シーン：**
- データベースアクセス権限申請（データベース所管部署の承認）
- システムアクセス申請（システム所管部署の承認）
- **ユーザー申請（対象ユーザー所属長承認）** ← resource_id にユーザーIDを設定

**設定例（データベースアクセス申請）：**
```sql
-- 申請タイプで resource_jurisdiction_column を設定
UPDATE M_APPLICATION_TYPE
SET resource_jurisdiction_column = 'owner_shozoku'
WHERE application_type_code = 'DB_ACCESS';

-- ワークフロー定義
INSERT INTO M_WORKFLOW_NODE_DEFINITION (
    node_definition_id, workflow_definition_id, node_seq,
    node_name, node_type, specific_node,
    is_required, approver_selection_required
) VALUES (
    SEQ_WORKFLOW_NODE_DEF.NEXTVAL, 1, 2,
    'データベース所管所属承認', 'jurisdiction_dept', NULL,
    'Y', 'Y'
);
```

**設定例（ユーザー申請 = 対象ユーザー所属長承認）：**
```sql
-- リソースにユーザーを使用
UPDATE M_APPLICATION_TYPE
SET resource_search_query = '
    SELECT user_cd AS resource_id,
           user_name AS resource_name,
           shozoku
    FROM e_imdb2_users
    WHERE user_cd LIKE :search_keyword || ''%''
',
resource_detail_query = '
    SELECT user_cd AS resource_id,
           user_name AS resource_name,
           shozoku
    FROM e_imdb2_users
    WHERE user_cd = :resource_id
',
resource_jurisdiction_column = 'shozoku'
WHERE application_type_code = 'USER_ACCOUNT';

-- ワークフロー定義
INSERT INTO M_WORKFLOW_NODE_DEFINITION (
    node_definition_id, workflow_definition_id, node_seq,
    node_name, node_type, specific_node,
    is_required, approver_selection_required
) VALUES (
    SEQ_WORKFLOW_NODE_DEF.NEXTVAL, 1, 2,
    '対象ユーザー所属長承認', 'jurisdiction_dept', NULL,
    'Y', 'Y'
);
```

**承認者取得ロジック：**
1. `application.jurisdiction_shozoku`（所管所属コード）を取得
   - `resource_jurisdiction_column` で指定されたカラムの値が自動設定される
2. `e_approver`テーブルから`department_cd`が一致するレコードを検索
3. `user_cd`を承認者として登録

**自動スキップ条件：**
- `applicant_shozoku == jurisdiction_shozoku`（申請者と所管が同じ所属）

**注：旧 `target_dept` ノードタイプについて**
- `target_dept` は削除されました
- リソースがユーザーの場合、`jurisdiction_dept` で代替可能です
- `resource_id` にユーザーIDを設定すれば、対象ユーザー所属長承認が実現できます

---

### 3. specific_node（特定ノード承認）

`M_NODE_APPROVER`テーブルで事前に定義された承認者が承認を行います。

**使用シーン：**
- システム企画室承認
- 情報セキュリティ委員会承認
- DBA承認

**設定例：**
```sql
-- ノード定義
INSERT INTO M_WORKFLOW_NODE_DEFINITION (
    node_definition_id, workflow_definition_id, node_seq,
    node_name, node_type, specific_node,
    is_required, approver_selection_required
) VALUES (
    SEQ_WORKFLOW_NODE_DEF.NEXTVAL, 1, 4,
    'システム企画室承認', 'specific_node', 'sys_planning',
    'Y', 'N'
);

-- 承認者定義
INSERT INTO M_NODE_APPROVER (
    node_approver_id, specific_node, approver_user_id, approver_order
) VALUES (
    SEQ_NODE_APPROVER.NEXTVAL, 'sys_planning', 't3_mori', 1
);
INSERT INTO M_NODE_APPROVER (
    node_approver_id, specific_node, approver_user_id, approver_order
) VALUES (
    SEQ_NODE_APPROVER.NEXTVAL, 'sys_planning', 't2_tanaka', 2
);
```

**承認者取得ロジック：**
1. `node_def.specific_value`（識別子）を取得
2. `M_NODE_APPROVER`テーブルから`specific_node`が一致するレコードを検索
3. `approver_user_id`を承認者として登録（`approver_order`順）

**スキップ条件：**
- `skip_condition`で任意の条件を設定可能

---

### 4. specific_dept（特定部署承認）★NEW

指定した部署コードの承認者が承認を行います。

**使用シーン：**
- 法務コンプライアンス部承認（department_cd='2310000'）
- 経営企画部承認
- 特定の部門長承認

**設定例：**
```sql
INSERT INTO M_WORKFLOW_NODE_DEFINITION (
    node_definition_id, workflow_definition_id, node_seq,
    node_name, node_type, specific_node,
    is_required, approver_selection_required
) VALUES (
    SEQ_WORKFLOW_NODE_DEF.NEXTVAL, 1, 5,
    '法務コンプライアンス部承認', 'specific_dept', '2310000',
    'Y', 'N'
);
```

**承認者取得ロジック：**
1. `node_def.specific_value`（部署コード）を取得
2. `e_approver`テーブルから`department_cd`が一致するレコードを検索
3. `user_cd`を承認者として登録

**スキップ条件：**
- `skip_condition`で任意の条件を設定可能

**specific_node vs specific_dept の違い：**

| 項目 | specific_node | specific_dept |
|------|---------------|---------------|
| 承認者定義 | `M_NODE_APPROVER`テーブル | `e_approver`テーブル |
| メンテナンス | ワークフローごとに設定 | 組織マスタと連動 |
| 使用例 | システム企画室、DBA | 法務部、経営企画部 |

---

### 5. resource_dept（リソース所管承認）★NEW

リソースIDと申請者所属をキーに、`specific_value`で指定したテーブル（またはView）から承認者を取得します。

**使用シーン：**
- Box フォルダアクセス権限申請
- 特定リソースに対して申請者所属ごとに異なる承認者を設定したい場合

**設定例：**
```sql
INSERT INTO M_WORKFLOW_NODE_DEFINITION (
    node_definition_id, workflow_definition_id, node_seq,
    node_name, node_type, specific_value,
    is_required, approver_selection_required
) VALUES (
    SEQ_WORKFLOW_NODE_DEF.NEXTVAL, 1, 3,
    'Boxフォルダ所管承認', 'resource_dept', 'nam_user_admin.boxex_approver',
    'Y', 'N'
);
```

**承認者取得ロジック：**
1. `node_def.specific_value`（テーブル名）を取得
2. `application.resource_id`（リソースID）を取得
3. `application.applicant_shozoku`（申請者所属コード）を取得
4. `specific_value`で指定されたテーブルから以下の条件でレコードを検索：
   - `resource_id = :resource_id`
   - `shozoku = :shozoku`
5. `approver`カラムの値を承認者として登録

**必須テーブル構造：**

`specific_value`で指定するテーブル（またはView）は、必ず以下の3カラムを持つ必要があります：

| カラム名 | 型 | 説明 |
|---------|-----|------|
| resource_id | VARCHAR2 | リソースID（T_APPLICATION.resource_idと一致） |
| shozoku | VARCHAR2 | 申請者所属コード |
| approver | VARCHAR2 | 承認者ユーザーID |

**設定例（nam_user_admin.boxex_approver）：**
```sql
CREATE TABLE nam_user_admin.boxex_approver (
    resource_id VARCHAR2(200),  -- 必須カラム
    shozoku VARCHAR2(20),       -- 必須カラム
    approver VARCHAR2(50),      -- 必須カラム
    start_date DATE,            -- 任意カラム（WHERE条件で使用可能）
    end_date DATE               -- 任意カラム（WHERE条件で使用可能）
);
```

**注意事項：**
- `specific_value`にはテーブル名（`schema.table`形式も可）を指定します
- テーブル/Viewには必ず`resource_id`, `shozoku`, `approver`の3カラムが必要です
- 有効期限などの追加条件が必要な場合は、Viewを作成して指定してください
- SQLインジェクション対策として、テーブル名には英数字とピリオド、アンダースコアのみ使用可能です

**スキップ条件：**
- `skip_condition`で任意の条件を設定可能
- 該当する承認者が存在しない場合は承認者が0人となる

**specific_dept vs resource_dept の違い：**

| 項目 | specific_dept | resource_dept |
|------|---------------|---------------|
| 承認者決定 | 部署コードのみ | リソースID + 申請者所属 |
| テーブル指定 | 固定（`e_approver`） | `specific_value`で指定 |
| 使用例 | 法務部承認 | Boxフォルダ所管承認 |

---

### 6. multiple_dept（複数所属長承認）★NEW

複数レコード申請で、変更される所属（`field_code='shozoku'`）の所属長が承認を行います。

**使用シーン：**
- メンバーの所属変更申請（複数レコード）
- ユーザーの所属異動申請（複数レコード）

**設定例：**
```sql
INSERT INTO M_WORKFLOW_NODE_DEFINITION (
    node_definition_id, workflow_definition_id, node_seq,
    node_name, node_type, specific_value,
    is_report_only, approver_selection_required
) VALUES (
    SEQ_WORKFLOW_NODE_DEF.NEXTVAL, 1, 2,
    '変更対象所属長承認', 'multiple_dept', NULL,
    'N', 'Y'  -- 複数所属の場合は承認者選択が推奨
);
```

**承認者取得ロジック：**
1. `M_APPLICATION_FIELD` から `field_code='shozoku'` の `field_id` を取得
2. `T_APPLICATION_DETAIL` から以下の条件でレコードを取得：
   - `application_id` が一致
   - `field_id` が上記で取得したID
   - `detail_action` が `'modify'`, `'add'`, `'delete'` のいずれか
3. 取得した各レコードの `field_value`（所属コード）から `e_approver` で承認者を取得
4. 承認者に `approver_group`（所属コード）を付与して登録

**並列承認ロジック（重要）：**
- 各承認者は `approver_group`（所属コード）でグループ分けされます
- **全ての所属グループから最低1人の承認が必要**です
- 同じグループ内の承認者は誰か一人が承認すればそのグループは承認完了となります

**動作例：**

申請内容（複数レコード）：
| detail_seq | detail_action | field_code | field_value |
|-----------|---------------|------------|-------------|
| 1 | modify | shozoku | 1234567 |
| 2 | add | shozoku | 2345678 |
| 3 | delete | shozoku | 3456789 |

承認者登録：
| approver_user_id | approver_group | is_notified | approved_at |
|------------------|----------------|-------------|-------------|
| user1 | 1234567 | Y | NULL |
| user2 | 1234567 | Y | NULL |
| user3 | 2345678 | Y | NULL |
| user4 | 2345678 | Y | NULL |
| user5 | 3456789 | Y | NULL |

承認の進行：
1. **user1が承認** → 所属1234567は承認完了（user2は承認不要）
2. **user4が承認** → 所属2345678は承認完了
3. **user5が承認** → 所属3456789は承認完了 → **ノード完了**

→ 各所属から最低1人承認されたので、次のノードへ進みます

**スキップ条件：**
- `skip_condition`で任意の条件を設定可能
- 変更される所属がない場合（`detail_action='none'` のみ）は承認者が0人となり自動スキップ

**注意事項：**
- **複数レコード申請専用**のノードタイプです
- 単一レコード申請では使用できません
- `field_code='shozoku'` のフィールドが定義されている必要があります
- 複数の所属が含まれる場合は `approver_selection_required='Y'` の設定を推奨
- 同一ユーザーが複数所属の承認者になる場合は、最初に検出された所属のグループに割り当てられます

---

### 7. report（報告）

承認ではなく、報告のみを行うノード。

**使用シーン：**
- 経営層への報告
- 監査ログ用の記録

**設定例：**
```sql
INSERT INTO M_WORKFLOW_NODE_DEFINITION (
    node_definition_id, workflow_definition_id, node_seq,
    node_name, node_type, specific_node,
    is_required, is_report_only, approver_selection_required
) VALUES (
    SEQ_WORKFLOW_NODE_DEF.NEXTVAL, 1, 100,
    '経営層への報告', 'report', 'executives',
    'N', 'Y', 'N'
);
```

**特徴：**
- `is_report_only='Y'`が設定される
- 報告完了を待たずに後続のノードが実行される

---

## 承認者選択（approver_selection_required）

`approver_selection_required='Y'`の場合、複数の承認者候補から申請者が実際の承認者を選択します。

**動作：**
1. 承認者候補が複数取得される
2. 申請提出時に承認者選択画面が表示される
3. 申請者が選択した承認者のみに通知が送られる（`is_notified='Y'`）

**適用可能なノードタイプ：**
- `applicant_dept`
- `target_dept`
- `jurisdiction_dept`
- `specific_node`
- `specific_dept`

---

## skip_condition（スキップ条件）

カスタム条件でノードをスキップできます。

詳細は [SKIP_CONDITION_EXAMPLES.md](SKIP_CONDITION_EXAMPLES.md) を参照。

**例：法務部承認を条件付きでスキップ**
```sql
UPDATE M_WORKFLOW_NODE_DEFINITION
SET skip_condition = 'fields.get(''contract_amount'', 0) < 1000000'
WHERE node_definition_id = 123;
```

---

## 未実装機能

以下のフィールドはDBスキーマに存在しますが、現在のロジックでは使用されていません（将来的な実装予定）。

### approver_selection_required（承認者選択フラグ）

**想定用途：**
- `'Y'` = 承認者選択：複数の承認者候補から申請者が承認者を選択
- `'N'` = 自動割り当て：承認者候補全員に通知（デフォルト動作）

**現状：**
- DBから取得しているが、申請提出時の承認者選択UIが未実装
- すべての承認者候補に自動的に通知される（`is_notified='Y'`）

**実装時の修正箇所：**
1. `app/templates/application/create.html` - 申請提出前に承認者選択UIを表示
2. `app/routes/application.py` - 選択された承認者のみ`is_notified='Y'`にセット
3. `app/services/workflow_service.py` - 承認者候補取得後、選択UIへ渡す処理

---

### is_report_only（報告専用フラグ）

**想定用途：**
- `'Y'` = 報告のみ：承認アクション不要、通知後すぐに次ノードへ進む
- `'N'` = 通常承認：承認・否認・差し戻しアクションが必要（デフォルト）

**現状：**
- DBから取得しているが、ワークフロー進行ロジックでは参照していない
- 報告ノードでも通常の承認ノードと同じ動作（承認待ち状態になる）

**実装時の修正箇所：**
1. `app/services/workflow_service.py` - ノードインスタンス作成後、`is_report_only='Y'`なら即座にステータスを`approved`に変更
2. `app/templates/approval/detail.html` - 報告ノードでは承認・否認ボタンを非表示
3. 通知メッセージ - 報告ノードと承認ノードで文言を変更（「承認してください」→「報告です」）

---

## まとめ

| ノードタイプ | 承認者の決定方法 | specific_value | 用途 |
|-------------|-----------------|----------------|------|
| `applicant_dept` | 申請者所属から動的取得 | 不要 | 申請者の上長承認 |
| `jurisdiction_dept` | 所管所属から動的取得 | 不要 | リソース所管部署承認<br>※リソースがユーザーの場合は対象ユーザー所属長承認 |
| `specific_node` | M_NODE_APPROVERから取得 | 識別子 | 固定メンバーの承認 |
| `specific_dept` | e_approverから部署で取得 | 部署コード | 特定部署の承認 |
| `resource_dept` | specific_valueで指定したテーブルから取得 | テーブル名 | リソース所管承認（Box等） |
| `multiple_dept` | T_APPLICATION_DETAILから動的取得 | 不要 | 複数レコード申請の変更所属承認 |
| `report` | M_NODE_APPROVERまたは既定 | 任意 | 報告のみ |
