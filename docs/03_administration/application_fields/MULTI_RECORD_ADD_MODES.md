# 複数レコード申請のレコード追加モード

複数レコード申請（`is_multi_record='Y'`）において、レコード追加時の動作を `record_add_mode` で制御できます。

## record_add_mode の値

| 値 | 名称 | 動作 | 用途例 |
|----|------|------|--------|
| `select` | 候補選択モード | `is_member='N'`のレコードから選択して追加 | Gmailグループメンバー管理、DBアクセス権限 |
| `free` | 自由入力モード | 空のフォーム行を追加して自由に入力 | 経費精算明細、契約条項、作業時間記録 |

---

## 動作の違い

### selectモード（デフォルト）

**設定：**
```sql
UPDATE M_APPLICATION_TYPE
SET record_add_mode = 'select'
WHERE application_type_id = 1;
```

**動作：**
1. `resource_member_query` で既存レコード（`is_member='Y'`）と追加候補（`is_member='N'`）を取得
2. 既存レコードは編集・削除が可能
3. **追加時**はキー項目（`is_key_field='Y'`）がドロップダウンになり、`is_member='N'`の候補から選択
4. キー項目を選択すると、他のフィールドが自動補完される（`data-field-*` 属性を利用）

**適用例：**
- **Gmailグループメンバー管理**
  - 既存メンバー：編集・削除
  - 追加：社員一覧から選択
  
- **データベースアクセス権限**
  - 既存：権限があるユーザー
  - 追加：権限がないユーザーから選択

**resource_member_query の例：**
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
  'Y' AS is_updatable  -- 既存レコードの編集可否
FROM users t
WHERE user_status = 'active'
ORDER BY is_member DESC, user_name
```

---

### freeモード

**設定：**
```sql
UPDATE M_APPLICATION_TYPE
SET record_add_mode = 'free'
WHERE application_type_id = 2;
```

**動作：**
1. `resource_member_query` の有無に関わらず、`available_records` は空リストとなる
2. 既存レコード（`is_member='Y'`）は通常通り表示・編集可能
3. **追加時**は完全に空のフォーム行が追加され、すべてのフィールドを手入力
4. キー項目も含めて自由入力（テキストボックス、数値入力、日付選択など）

**適用例：**
- **経費精算の明細入力**
  - 既存明細：修正・削除
  - 追加：日付、費目、金額などを自由入力
  
- **契約条項の複数登録**
  - 既存条項：編集・削除
  - 追加：条項番号、内容、期限などを自由入力

**resource_member_query の扱い：**
- `resource_member_query` が設定されていても、`available_records` は無視される
- 既存レコード（`is_member='Y'`）の取得には引き続き使用される
- `resource_member_query` が `NULL` の場合は既存レコードなし（完全に新規入力のみ）

---

## 画面の違い

### selectモード

```
既存レコード
┌─────────────────────────────────────┐
│ メールアドレス │ 権限  │ アクション │
├─────────────────────────────────────┤
│ user1@nam.jp   │ 編集者│ 変更なし   │
│ user2@nam.jp   │ 閲覧者│ 編集       │
└─────────────────────────────────────┘

レコード追加
┌─────────────────────────────────────┐
│ メールアドレス │ 権限  │ アクション │
├─────────────────────────────────────┤
│ [選択してください ▼] │ [編集者▼] │ 追加 │
│  - user3@nam.jp                     │
│  - user4@nam.jp                     │
└─────────────────────────────────────┘
```

キー項目（メールアドレス）はドロップダウン

---

### freeモード

```
既存レコード
┌─────────────────────────────────────┐
│ 日付       │ 費目   │ 金額  │ アクション │
├─────────────────────────────────────┤
│ 2026-05-20 │ 交通費 │ 1,200 │ 変更なし   │
│ 2026-05-21 │ 会議費 │ 3,500 │ 編集       │
└─────────────────────────────────────┘

レコード追加
┌─────────────────────────────────────┐
│ 日付       │ 費目   │ 金額  │ アクション │
├─────────────────────────────────────┤
│ [________] │ [____] │ [___] │ 追加       │
└─────────────────────────────────────┘
```

すべてのフィールドが手入力

---

## 実装の仕組み

### テンプレート側（multi_record.html / multi_record_edit.html）

```jinja2
{% if field.is_key_field == 'Y' and field.field_type == 'select' and app_type.record_add_mode == 'select' %}
    <!-- selectモード：候補から選択 -->
    <select name="records[${rowCounter}][field_{{ field.field_id }}]" data-key-field="true">
        <option value="">選択してください</option>
        {% for record in available_records %}
        <option value="{{ record[field.resource_column_name] }}" ...>
            {{ record[field.resource_column_name] }}
        </option>
        {% endfor %}
    </select>
{% elif field.field_type == 'text' %}
    <!-- freeモード または 非キー項目：自由入力 -->
    <input type="text" name="records[${rowCounter}][field_{{ field.field_id }}]">
{% endif %}
```

**ポイント：**
- `app_type.record_add_mode == 'select'` の条件を追加
- `'select'` の場合のみキー項目がドロップダウンになる
- `'free'` の場合はキー項目も通常の入力フィールドになる

---

### サーバー側（application_multi.py）

```python
# record_add_mode が 'free' の場合は available_records を空にする
if app_type.get('record_add_mode') == 'free':
    available_records = []
    current_app.logger.info('[multi_record] record_add_mode=free: 自由入力モード')
else:
    available_records = [r for r in all_records if r.get('is_member') == 'N']
    current_app.logger.info('[multi_record] record_add_mode=select: 候補選択モード')
```

**ポイント：**
- `'free'` の場合は `available_records` を強制的に空リストにする
- テンプレート側で `available_records` が空なら候補なし→自由入力にフォールバック

---

## バリデーション

### selectモード

- キー項目が候補リストに存在するかチェック（サーバー側で検証）
- `unique_in_table` などのバリデーションは実行

### freeモード

- 通常のバリデーションルールを適用（`required`, `unique_in_table`, `pattern` など）
- キー項目の候補チェックは行わない（自由入力のため）

---

## 移行手順

既存の複数レコード申請を `free` モードに変更する場合：

1. **DDLを実行**
   ```sql
   -- database/27_add_record_add_mode.sql を実行
   ```

2. **申請タイプを更新**
   ```sql
   UPDATE M_APPLICATION_TYPE
   SET record_add_mode = 'free'
   WHERE application_type_id = <対象のID>;
   COMMIT;
   ```

3. **動作確認**
   - 既存レコードが表示されるか
   - 「レコード追加」で空のフォームが追加されるか
   - フィールドが自由入力できるか

---

## まとめ

| 項目 | selectモード | freeモード |
|------|-------------|-----------|
| デフォルト | ○ | × |
| resource_member_query | 必須 | 任意（既存レコード表示用） |
| キー項目の入力方法 | ドロップダウン選択 | 自由入力 |
| 用途 | 既存データから選んで追加 | 完全に新しいデータを入力 |
| 例 | メンバー追加、権限付与 | 明細入力、項目登録 |

設計のポイント：
- **選択式が適切**な場合は `'select'`（ユーザー、グループ、リソースなど既存マスタから選ぶ）
- **入力式が適切**な場合は `'free'`（金額、日時、自由記述など毎回異なる値）
