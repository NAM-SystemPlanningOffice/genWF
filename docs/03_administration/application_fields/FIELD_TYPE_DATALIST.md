# datalist フィールドタイプ

## 概要

`datalist` フィールドタイプは、HTML5の `<input>` + `<datalist>` を使用した、**プルダウン候補を表示しつつ自由入力も可能**なフィールドです。

## selectとの違い

| 項目 | select | datalist |
|------|--------|----------|
| 入力方法 | 選択肢からのみ選択 | 選択肢から選択 or 自由入力 |
| 制約 | 厳密（選択肢にない値は入力不可） | 柔軟（選択肢にない値も入力可） |
| UI | ドロップダウン | テキストボックス + サジェスト |
| 使用例 | 性別、所属（固定リスト） | 部署名、役職（柔軟に入力したい） |

## 設定方法

### 1. フィールドタイプを `datalist` に設定

```sql
UPDATE M_APPLICATION_FIELD
SET field_type = 'datalist'
WHERE field_code = 'department_name';
```

### 2. プルダウングループを設定（selectと同じ）

#### 静的プルダウン（M_PULLDOWN_OPTION）

```sql
-- プルダウングループを作成
INSERT INTO M_PULLDOWN_GROUP (pulldown_group_id, group_name)
VALUES (10, '部署名候補');

-- 選択肢を登録
INSERT INTO M_PULLDOWN_OPTION (option_id, pulldown_group_id, option_value, option_label, display_order)
VALUES (101, 10, 'システム企画室', 'システム企画室', 1);

INSERT INTO M_PULLDOWN_OPTION (option_id, pulldown_group_id, option_value, option_label, display_order)
VALUES (102, 10, '経営企画部', '経営企画部', 2);

-- フィールドに紐付け
UPDATE M_APPLICATION_FIELD
SET pulldown_group_id = 10,
    pulldown_is_dynamic = 'N'
WHERE field_code = 'department_name';
```

#### 動的プルダウン（SQLクエリ）

```sql
UPDATE M_APPLICATION_FIELD
SET pulldown_is_dynamic = 'Y',
    pulldown_dynamic_query = '
        SELECT DISTINCT shozoku_name AS option_value,
                        shozoku_name AS option_label
        FROM e_imdb2_users
        WHERE shozoku_name IS NOT NULL
        ORDER BY shozoku_name
    '
WHERE field_code = 'department_name';
```

## 動的プルダウンでのバインド変数

動的プルダウンクエリで以下のバインド変数が使用可能です：

| バインド変数 | 説明 | 例 |
|-------------|------|-----|
| `:applicant_user_id` | 申請者のユーザーID | `'user001'` |
| `:applicant_shozoku` | 申請者の所属コード | `'1234567'` |
| `:resource_id` | 対象リソースのID（新規作成時はNULL） | `'DB001'` |

### 使用例

**申請者の所属メンバーのみを候補に表示**

```sql
UPDATE M_APPLICATION_FIELD
SET pulldown_is_dynamic = 'Y',
    pulldown_dynamic_query = '
        SELECT user_cd AS option_value,
               user_name AS option_label
        FROM e_imdb2_users
        WHERE shozoku = :applicant_shozoku
          AND user_cd IS NOT NULL
        ORDER BY user_cd
    '
WHERE field_code = 'target_user';
```

**リソースに関連するメンバーを候補に表示**

```sql
UPDATE M_APPLICATION_FIELD
SET pulldown_is_dynamic = 'Y',
    pulldown_dynamic_query = '
        SELECT member_id AS option_value,
               member_name AS option_label
        FROM resource_members
        WHERE resource_id = :resource_id
        ORDER BY member_name
    '
WHERE field_code = 'member';
```

## 画面での動作

### 新規申請画面
- テキストボックスとして表示
- 入力開始すると、候補がサジェスト表示される
- 候補を選択するか、自由に入力可能

### 編集画面
- 既存値が表示される（候補にない値でもOK）
- 候補を参考にしつつ、値を変更可能

### 複数レコード画面
- 各行で独立したdatalistが表示される
- レコードごとに異なる値を入力可能

## バリデーション

datalistフィールドは自由入力を許可するため、必要に応じてバリデーションを設定してください：

```sql
-- 文字数制限
INSERT INTO M_FIELD_VALIDATION (validation_id, field_id, validation_rule_id, apply_on_create)
SELECT SEQ_FIELD_VALIDATION.NEXTVAL, field_id, 1, 'Y'
FROM M_APPLICATION_FIELD
WHERE field_code = 'department_name';

-- 正規表現パターン（カタカナのみ、など）
INSERT INTO M_FIELD_VALIDATION (validation_id, field_id, validation_rule_id, validation_parameter, apply_on_create)
SELECT SEQ_FIELD_VALIDATION.NEXTVAL, field_id, 5, '^[ァ-ヶー]+$', 'Y'
FROM M_APPLICATION_FIELD
WHERE field_code = 'department_name';
```

## まとめ

- **select**: 選択肢を厳密に制御したい場合
- **datalist**: 候補を提示しつつ柔軟に入力させたい場合

部署名、役職、タグなど、ある程度パターンはあるが固定リストにしたくない項目に最適です。
