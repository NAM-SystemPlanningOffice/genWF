# 申請区分と機能設計

## 1. 申請区分の概要

申請には以下の3つの区分があります。

| 申請区分 | コード | 説明 |
|---------|-------|------|
| 新規作成 | create | 既存に存在しないリソースの新規作成申請 |
| 修正 | modify | 既存リソースの属性変更申請 |
| 削除 | delete | 既存リソースの削除申請 |

## 2. 申請区分ごとの機能差異

### A. 新規作成（create）

#### 特徴
- 既存リソースとの重複チェックが必須
- すべてのフィールドを入力
- 既存設定からの値のコピーは不要

#### 画面機能
1. **申請種類選択**
   - 申請種類を選択
   - 「新規作成」を選択

2. **入力フォーム**
   - すべてのフィールドを表示
   - 必須項目は`is_required_create='Y'`のフィールド
   - プルダウンやバリデーションが適用される

3. **重複チェック**
   - 入力値が既存リソースと重複しないかチェック
   - `M_APPLICATION_TYPE.resource_validation_query`に設定されたSQLで検証
   - 例: Gmailグループの場合、グループメールアドレスが既存と重複しないか

4. **一時保存**
   - 申請ステータス='draft'で保存
   - 後で編集可能

5. **申請提出**
   - バリデーション実行
   - 重複チェック実行
   - 申請ステータス='submitted'に更新
   - ワークフロー開始

#### データベース
```sql
-- T_APPLICATION
action_type = 'create'
reference_resource_id = NULL
```

---

### B. 修正（modify）

#### 特徴
- 既存リソースの選択が必要
- 既存設定値を取得して表示
- 変更可能フィールドと変更不可フィールドが存在
- 変更後の値が他のリソースと重複しないかチェック

#### 画面機能
1. **申請種類選択**
   - 申請種類を選択
   - 「修正」を選択

2. **既存リソース検索・選択**
   - `M_APPLICATION_TYPE.resource_search_query`に設定されたSQLで既存リソースを検索
   - 検索条件（例: グループ名の部分一致、所管所属など）を入力
   - 検索結果一覧を表示
   - 修正対象リソースを選択

3. **既存設定値の取得**
   - `M_APPLICATION_TYPE.resource_detail_query`に設定されたSQLで詳細を取得
   - 各フィールドに既存値を自動設定
   - `M_APPLICATION_FIELD.resource_column_name`に対応するカラムの値を取得

4. **入力フォーム**
   - `is_editable_modify='Y'`のフィールドのみ編集可能
   - `is_editable_modify='N'`のフィールドは読み取り専用（グレーアウト）
   - 必須項目は`is_required_modify='Y'`のフィールド

5. **変更内容の確認**
   - 変更前と変更後の差分を表示
   - 変更されたフィールドのみハイライト

6. **重複チェック**
   - 変更後の値が他のリソースと重複しないかチェック
   - 自分自身（修正対象）は重複チェック対象外

7. **申請提出**
   - バリデーション実行
   - ワークフロー開始

#### データベース
```sql
-- T_APPLICATION
action_type = 'modify'
reference_resource_id = '修正対象のリソースID' -- 例: 'group@example.com'

-- T_APPLICATION_DETAIL
-- 変更後の値を保存（変更されたフィールドのみ、または全フィールド）
```

---

### C. 削除（delete）

#### 特徴
- 既存リソースの選択が必要
- 既存設定値を表示（すべて読み取り専用）
- 削除理由の入力が必要
- フィールドの編集は不要

#### 画面機能
1. **申請種類選択**
   - 申請種類を選択
   - 「削除」を選択

2. **既存リソース検索・選択**
   - 修正と同様の検索機能
   - 削除対象リソースを選択

3. **既存設定値の表示**
   - すべてのフィールドを読み取り専用で表示
   - 削除対象の内容を確認

4. **削除理由の入力**
   - 削除理由フィールド（必須）
   - テキストエリアで複数行入力可能

5. **削除確認**
   - 削除対象の内容と削除理由を確認
   - 確認メッセージを表示

6. **申請提出**
   - ワークフロー開始

#### データベース
```sql
-- T_APPLICATION
action_type = 'delete'
reference_resource_id = '削除対象のリソースID'
remarks = '削除理由'

-- T_APPLICATION_DETAIL
-- 削除時は既存値を保存（承認者が削除対象を確認できるように）
```

---

## 3. SQLクエリの設計

### M_APPLICATION_TYPE のクエリカラム

#### resource_search_query
既存リソースを検索するためのSQL。

**要件**:
- SELECT文でリソース一覧を取得
- 検索条件はプレースホルダー（:param）で指定
- 結果には`resource_id`, `display_label`カラムを含む

**例（Gmailグループ）**:
```sql
SELECT 
    resource_id,
    group_name || ' (' || group_email || ')' AS display_label,
    group_email,
    owner_shozoku,
    member_count
FROM T_RESOURCE_GMAIL_GROUP
WHERE is_active = 'Y'
  AND (:search_keyword IS NULL OR group_name LIKE '%' || :search_keyword || '%' OR group_email LIKE '%' || :search_keyword || '%')
  AND (:owner_shozoku IS NULL OR owner_shozoku = :owner_shozoku)
ORDER BY group_name
```

#### resource_detail_query
選択されたリソースの詳細を取得するSQL。

**要件**:
- SELECT文で単一リソースの詳細を取得
- WHERE句で`:resource_id`を条件指定
- カラム名は`M_APPLICATION_FIELD.resource_column_name`と対応

**例（Gmailグループ）**:
```sql
SELECT 
    resource_id,
    group_name,
    group_email,
    description,
    owner_shozoku,
    member_count
FROM T_RESOURCE_GMAIL_GROUP
WHERE resource_id = :resource_id
```

#### resource_validation_query
重複チェックのためのSQL。

**要件**:
- SELECT文で重複の有無を確認（COUNT(*)等）
- 検証対象の値をプレースホルダーで指定
- 修正の場合は自分自身を除外（`:exclude_resource_id`）

**例（Gmailグループ - メールアドレス重複チェック）**:
```sql
SELECT COUNT(*) AS duplicate_count
FROM T_RESOURCE_GMAIL_GROUP
WHERE group_email = :group_email
  AND is_active = 'Y'
  AND (:exclude_resource_id IS NULL OR resource_id != :exclude_resource_id)
```

---

## 4. フィールド定義の設計パターン

### 例: Gmailグループ申請

#### グループメールアドレス（変更不可）
```
field_code: group_email
field_name: グループメールアドレス
field_type: text
is_required_create: Y
is_required_modify: Y
is_required_delete: Y
is_editable_modify: N  -- 修正時は変更不可
resource_column_name: group_email
```

#### グループ名（変更可）
```
field_code: group_name
field_name: グループ名
field_type: text
is_required_create: Y
is_required_modify: Y
is_required_delete: Y
is_editable_modify: Y  -- 修正時は変更可
resource_column_name: group_name
```

#### 説明（変更可）
```
field_code: description
field_name: 説明
field_type: textarea
is_required_create: N
is_required_modify: N
is_required_delete: Y
is_editable_modify: Y  -- 修正時は変更可
resource_column_name: description
```

---

## 5. 画面フロー

### 新規作成フロー
```
[申請種類選択] 
    ↓
[申請区分選択: 新規作成]
    ↓
[入力フォーム]
    ↓
[重複チェック]
    ↓
[確認画面]
    ↓
[申請提出] → [ワークフロー開始]
```

### 修正フロー
```
[申請種類選択]
    ↓
[申請区分選択: 修正]
    ↓
[既存リソース検索]
    ↓
[検索結果一覧]
    ↓
[リソース選択]
    ↓
[既存値自動入力された入力フォーム]
    ↓
[変更内容確認]
    ↓
[重複チェック（変更されたフィールドのみ）]
    ↓
[確認画面（差分表示）]
    ↓
[申請提出] → [ワークフロー開始]
```

### 削除フロー
```
[申請種類選択]
    ↓
[申請区分選択: 削除]
    ↓
[既存リソース検索]
    ↓
[検索結果一覧]
    ↓
[リソース選択]
    ↓
[削除対象確認（読み取り専用）]
    ↓
[削除理由入力]
    ↓
[確認画面]
    ↓
[申請提出] → [ワークフロー開始]
```

---

## 6. 実装上の考慮事項

### バリデーション
- 新規作成: すべての必須フィールドと重複チェック
- 修正: 変更されたフィールドのみバリデーションと重複チェック
- 削除: 削除理由の必須チェック

### 画面表示制御
- フィールドの表示/非表示は申請区分により動的に制御
- 編集可/不可はCSSクラスで視覚的に区別（readonly, disabled属性）

### エラーハンドリング
- リソーステーブルが更新中の場合のロック制御
- 申請提出時と承認時のタイムラグによるデータ不整合対策
- 重複チェック時の排他制御

### パフォーマンス
- リソース検索のページネーション
- 検索結果の件数制限（例: 最大1000件）
- インデックスの適切な設定
