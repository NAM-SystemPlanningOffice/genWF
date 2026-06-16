# 申請対象ユーザーと所管所属の設計

## 1. 申請の分類

申請は「申請対象ユーザーの有無」と「所管所属の関与」により分類されます。

### A. ユーザーに関わらない申請

リソース（システム、グループ等）自体の設定変更を申請する。

#### 特徴
- 申請対象ユーザーは存在しない
- リソースの所管所属が重要
- 申請可能な所属に制限がある場合が多い

#### 例
1. **Gmailグループの新設・変更・削除**
   - 申請内容: グループ名、メールアドレス、説明等
   - 申請対象ユーザー: なし
   - 所管所属: グループを管理する所属
   - 申請可能所属: 所管所属のみ
   - 承認フロー:
     ```
     [申請者の所属長] → [システム企画室] → [承認完了]
     ```
   - 注意: 申請者の所属 = 所管所属であることが前提

2. **Google Driveフォルダの作成・権限設定**
   - 申請内容: フォルダ名、親フォルダ、権限設定等
   - 申請対象ユーザー: なし
   - 所管所属: フォルダを管理する所属
   - 申請可能所属: 所管所属のみ

3. **Azureリソースグループの作成**
   - 申請内容: リソースグループ名、リージョン、タグ等
   - 申請対象ユーザー: なし
   - 所管所属: リソースグループを管理する所属
   - 申請可能所属: 特定の所属のみ

#### データ構造
```sql
-- T_APPLICATION
applicant_user_id: '申請者ID'
applicant_shozoku: '申請者の所属（=所管所属）'
target_user_id: NULL
target_shozoku: NULL
jurisdiction_shozoku: '所管所属コード'

-- M_APPLICATION_TYPE
has_target_user: 'N'
requires_jurisdiction: 'Y'
jurisdiction_restriction: 'jurisdiction_only'  -- 所管所属からのみ申請可能
```

---

### B. ユーザーに関わる申請（所管なし）

特定ユーザーの権限や設定を申請する。リソース自体に所管所属の概念がない。

#### 特徴
- 申請対象ユーザーが明確に存在する
- 申請対象ユーザーの所属長承認が必須
- リソースに所管所属の概念がない

#### 例
1. **ユーザーのメールエイリアス追加**
   - 申請内容: エイリアスメールアドレス
   - 申請対象ユーザー: あり
   - 所管所属: なし
   - 申請可能所属: 申請対象ユーザーの所属のみ
   - 承認フロー:
     ```
     [申請対象ユーザーの所属長] → [システム企画室] → [承認完了]
     ```

2. **ユーザーのMicrosoft 365ライセンス変更**
   - 申請内容: ライセンス種別
   - 申請対象ユーザー: あり
   - 所管所属: なし

#### データ構造
```sql
-- T_APPLICATION
applicant_user_id: '申請者ID'
applicant_shozoku: '申請者の所属'
target_user_id: '申請対象ユーザーID'
target_shozoku: '申請対象ユーザーの所属'
jurisdiction_shozoku: NULL

-- M_APPLICATION_TYPE
has_target_user: 'Y'
requires_jurisdiction: 'N'
jurisdiction_restriction: 'any'  -- 制限なし（同一所属内であれば申請可）
```

---

### C. ユーザーに関わる申請（所管あり）

特定ユーザーに対して、所管所属が管理するリソースへのアクセス権限等を申請する。

#### 特徴
- 申請対象ユーザーが明確に存在する
- リソースに所管所属が存在する
- 申請対象ユーザーの所属長承認 + 所管所属長承認が必要（所属が異なる場合）

#### 例
1. **データベースアクセス権限申請**
   - 申請内容: データベース名、スキーマ、権限レベル（READ/WRITE）
   - 申請対象ユーザー: あり（権限を付与するユーザー）
   - 所管所属: データベースを管理する所属
   - 申請可能所属: 申請対象ユーザーの所属
   - 承認フロー（申請者の所属 ≠ データベースの所管の場合）:
     ```
     [申請対象ユーザーの所属長] → [データベース所管の所属長] → [システム企画室] → [承認完了]
     ```
   - 承認フロー（申請者の所属 = データベースの所管の場合）:
     ```
     [申請対象ユーザーの所属長] → [システム企画室] → [承認完了]
     ```
     ※所管承認は省略（同一所属のため）

2. **Azureリソースへのアクセス権限申請**
   - 申請内容: リソースグループ、ロール（Reader/Contributor等）
   - 申請対象ユーザー: あり
   - 所管所属: リソースグループを管理する所属

3. **共有フォルダへのアクセス権限申請**
   - 申請内容: フォルダパス、権限レベル
   - 申請対象ユーザー: あり
   - 所管所属: フォルダを管理する所属

#### データ構造
```sql
-- T_APPLICATION
applicant_user_id: '申請者ID'
applicant_shozoku: '申請者の所属（=申請対象ユーザーの所属）'
target_user_id: '申請対象ユーザーID'
target_shozoku: '申請対象ユーザーの所属'
jurisdiction_shozoku: 'リソースの所管所属コード'

-- M_APPLICATION_TYPE
has_target_user: 'Y'
requires_jurisdiction: 'Y'
jurisdiction_restriction: 'any'  -- 任意の所属から申請可能（申請対象ユーザーの所属と一致する必要あり）
```

---

## 2. 申請可能所属の制限

### jurisdiction_restriction の値と意味

| 値 | 意味 | 例 |
|----|------|-----|
| any | 制限なし（同一所属内であれば申請可） | ユーザーのライセンス変更 |
| jurisdiction_only | 所管所属からのみ申請可能 | Gmailグループの管理、Google Driveフォルダの管理 |
| specific | 特定の所属リストからのみ申請可能 | Azureリソースグループの作成（特定部署のみ） |

### 申請時のチェックロジック

#### ケース1: has_target_user='N', jurisdiction_restriction='jurisdiction_only'
（例: Gmailグループの新設）

```python
# 申請時のチェック
if applicant_shozoku != jurisdiction_shozoku:
    raise ValidationError("この申請は所管所属からのみ申請可能です。")
```

#### ケース2: has_target_user='Y', jurisdiction_restriction='any'
（例: メールエイリアス追加）

```python
# 申請時のチェック
if applicant_shozoku != target_shozoku:
    # 同一所属内メンバーの代理申請チェック
    if not is_same_shozoku_member(applicant_user_id, target_user_id):
        raise ValidationError("申請対象ユーザーと同一所属のメンバーのみ申請可能です。")
```

#### ケース3: has_target_user='Y', requires_jurisdiction='Y'
（例: データベースアクセス権限申請）

```python
# 申請時のチェック
if applicant_shozoku != target_shozoku:
    raise ValidationError("申請対象ユーザーと同一所属からのみ申請可能です。")

# jurisdiction_shozokuは入力値またはリソース選択時に自動設定
# 所管承認の要否は承認フロー開始時に判定
```

---

## 3. 承認フローの動的制御

### 所管承認ノードのスキップ条件

ワークフローノード定義で、所管承認ノードに以下のスキップ条件を設定。

```sql
-- M_WORKFLOW_NODE_DEFINITION
node_type: 'jurisdiction_dept'
skip_condition: 'applicant_shozoku = jurisdiction_shozoku'
```

### ワークフロー実行時の判定ロジック

```python
def should_skip_node(node_definition, application):
    """ノードをスキップすべきか判定"""
    if not node_definition.skip_condition:
        return False
    
    # skip_conditionのSQL式を評価
    # 例: "applicant_shozoku = jurisdiction_shozoku"
    condition_sql = node_definition.skip_condition
    
    # プレースホルダーを実際の値に置き換え
    context = {
        'applicant_shozoku': application.applicant_shozoku,
        'target_shozoku': application.target_shozoku,
        'jurisdiction_shozoku': application.jurisdiction_shozoku,
        'application_type_id': application.application_type_id,
    }
    
    # 条件評価（簡易実装例）
    return eval_condition(condition_sql, context)
```

---

## 4. リソーステーブルの所管所属管理

### 所管所属カラムの追加

リソーステーブルには必ず所管所属を格納するカラムを含める。

#### 例: T_RESOURCE_GMAIL_GROUP

| カラム名 | 型 | 説明 |
|---------|-----|------|
| resource_id | VARCHAR2(200) | リソースID（グループメールアドレス） |
| group_name | VARCHAR2(200) | グループ名 |
| group_email | VARCHAR2(200) | グループメールアドレス |
| owner_shozoku | VARCHAR2(20) | 所管所属コード ← これ |
| ... | ... | ... |

#### 例: T_RESOURCE_DATABASE

| カラム名 | 型 | 説明 |
|---------|-----|------|
| resource_id | VARCHAR2(200) | データベース識別子 |
| database_name | VARCHAR2(200) | データベース名 |
| database_type | VARCHAR2(50) | データベース種別（Oracle/SQL Server等） |
| admin_shozoku | VARCHAR2(20) | 管理所管所属コード ← これ |
| ... | ... | ... |

### M_APPLICATION_TYPE での設定

```sql
-- Gmailグループの例
INSERT INTO M_APPLICATION_TYPE (
    application_type_code,
    application_type_name,
    has_target_user,
    requires_jurisdiction,
    jurisdiction_restriction,
    resource_table_name,
    resource_jurisdiction_column
) VALUES (
    'GMAIL_GROUP',
    'Gmailグループ管理',
    'N',  -- ユーザーに関わらない
    'Y',  -- 所管所属必須
    'jurisdiction_only',  -- 所管所属からのみ申請可能
    'T_RESOURCE_GMAIL_GROUP',
    'owner_shozoku'  -- 所管所属カラム名
);

-- データベースアクセス権限の例
INSERT INTO M_APPLICATION_TYPE (
    application_type_code,
    application_type_name,
    has_target_user,
    requires_jurisdiction,
    jurisdiction_restriction,
    resource_table_name,
    resource_jurisdiction_column
) VALUES (
    'DB_ACCESS_PERMISSION',
    'データベースアクセス権限申請',
    'Y',  -- ユーザーに関わる
    'Y',  -- 所管所属必須
    'any',  -- 任意の所属から申請可能（ユーザー所属と一致要）
    'T_RESOURCE_DATABASE',
    'admin_shozoku'  -- 所管所属カラム名
);
```

---

## 5. 画面での所管所属の扱い

### ユーザーに関わらない申請（Gmailグループ等）

#### 新規作成
```
[申請種類選択: Gmailグループ管理]
    ↓
[申請区分選択: 新規作成]
    ↓
[所管所属の確認]
    ← 申請者の所属を自動設定（変更不可）
    ← 申請者の所属以外からは申請不可
    ↓
[入力フォーム]
    - グループ名
    - グループメールアドレス
    - 説明
    - ...
    ↓
[申請提出]
```

#### 修正・削除
```
[申請種類選択: Gmailグループ管理]
    ↓
[申請区分選択: 修正/削除]
    ↓
[既存グループ検索]
    ← 所管所属フィルタ: 申請者の所属のみ
    ↓
[グループ選択]
    ← 申請者の所属が所管のグループのみ表示
    ↓
[入力フォーム/確認]
    ↓
[申請提出]
```

### ユーザーに関わる申請（データベースアクセス権限等）

#### 新規作成
```
[申請種類選択: データベースアクセス権限申請]
    ↓
[申請区分選択: 新規作成]
    ↓
[申請対象ユーザー選択]
    ← 同一所属のメンバーから選択
    ↓
[データベース選択]
    ← リソース検索（全データベース）
    ← 選択したデータベースの所管所属を自動取得
    ↓
[権限レベル選択]
    - READ
    - WRITE
    - ADMIN
    ↓
[確認画面]
    - 申請対象ユーザー: ○○（所属: XX部）
    - データベース: △△（所管: YY部）
    ← 所管が異なる場合は「YY部の承認が必要です」と表示
    ↓
[申請提出]
```

---

## 6. 承認者への表示

承認画面では、申請の種類に応じて表示を変える。

### ユーザーに関わらない申請

```
【申請内容】
申請種類: Gmailグループ管理
申請区分: 新規作成
申請者: 山田太郎（所属: システム企画室）
所管所属: システム企画室

【申請詳細】
グループ名: システム企画室ML
グループメールアドレス: sys-planning@example.com
説明: システム企画室の全体ML
```

### ユーザーに関わる申請

```
【申請内容】
申請種類: データベースアクセス権限申請
申請区分: 新規作成
申請者: 山田太郎（所属: システム企画室）
申請対象ユーザー: 佐藤花子（所属: システム企画室）
リソース所管: データベース管理部

【申請詳細】
データベース名: 顧客管理DB
スキーマ: CUSTOMER
権限レベル: READ

【承認フロー】
1. ✓ システム企画室長承認（完了）
2. → データベース管理部長承認（現在のノード）← 所管が異なるため必要
3. - システム企画室承認（最終）
```

---

## 7. 実装上の考慮事項

### 所管所属の取得タイミング

1. **新規作成時（ユーザーに関わらない）**
   - 申請者の所属を自動設定
   - `jurisdiction_shozoku = applicant_shozoku`

2. **修正・削除時**
   - リソーステーブルから取得
   - `resource_detail_query`で`resource_jurisdiction_column`の値を取得

3. **新規作成時（ユーザーに関わる、所管あり）**
   - リソース選択時にリソーステーブルから取得
   - 例: データベース選択時に`admin_shozoku`を取得

### エラーハンドリング

```python
# 所管所属からの申請かチェック
def validate_jurisdiction_restriction(application_type, applicant_shozoku, jurisdiction_shozoku):
    if application_type.jurisdiction_restriction == 'jurisdiction_only':
        if applicant_shozoku != jurisdiction_shozoku:
            raise ValidationError(
                f"この申請は所管所属（{jurisdiction_shozoku}）からのみ申請可能です。"
            )
    elif application_type.jurisdiction_restriction == 'specific':
        allowed_list = application_type.allowed_shozoku_list.split(',')
        if applicant_shozoku not in allowed_list:
            raise ValidationError(
                f"この申請は特定の所属からのみ申請可能です。"
            )
```

### 承認者の取得

```python
def get_approvers_for_node(node_definition, application):
    """ノードの承認者候補を取得"""
    if node_definition.node_type == 'applicant_dept':
        # 申請者の所属長
        return get_approvers_by_shozoku(application.applicant_shozoku)
    
    elif node_definition.node_type == 'target_dept':
        # 申請対象ユーザーの所属長
        return get_approvers_by_shozoku(application.target_shozoku)
    
    elif node_definition.node_type == 'jurisdiction_dept':
        # 所管所属長
        return get_approvers_by_shozoku(application.jurisdiction_shozoku)
    
    elif node_definition.node_type == 'specific_dept':
        # 特定所属（マスタで定義）
        return get_approvers_by_shozoku(node_definition.specific_shozoku)
    
    elif node_definition.node_type == 'final':
        # 最終承認者（マスタで定義）
        return get_final_approvers()
```
