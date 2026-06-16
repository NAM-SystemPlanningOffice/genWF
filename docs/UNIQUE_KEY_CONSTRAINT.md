# 複数フィールドの複合ユニークキー制約

## 概要

複数レコード申請において、`is_key_field='Y'` のフィールドすべての組み合わせで重複を検出し、エラーを表示します。

## 動作

### 対象フィールド

`M_APPLICATION_FIELD.is_key_field='Y'` のフィールドすべてが対象です。

**例：**
- `user_id` (is_key_field='Y')
- `shozoku` (is_key_field='Y')

→ `(user_id, shozoku)` の組み合わせでユニーク制約

### チェックタイミング

#### 1. クライアントサイド（リアルタイム）

キーフィールドの値が変更されたタイミングで重複チェックを実行：

- **text/number/datalist**: `oninput` イベント
- **select/date**: `onchange` イベント

重複が検出された場合：
- 画面上部に赤いエラーメッセージを表示
- 送信ボタンを無効化（`disabled`）

**エラー表示例：**
```
⚠️ 重複エラー
キーフィールド（ユーザーID, 所属コード）の組み合わせが重複しています。
レコード番号 1 と 3 が同じ値です。
```

#### 2. サーバーサイド（保存時）

念のため、サーバー側でも最終チェックを実施：

- 保存前に全レコードのキーフィールドを検証
- 重複があれば保存を拒否し、エラーメッセージを表示

**エラーメッセージ例：**
```
キーフィールド（ユーザーID, 所属コード）の組み合わせが重複しています。
```

### 除外条件

以下のレコードは重複チェックの対象外です：

1. **削除予定のレコード** (`detail_action='delete'`)
2. **すべてのキーフィールドが空のレコード**

## 実装箇所

### クライアントサイド（JavaScript）

- [app/templates/application/multi_record.html](../app/templates/application/multi_record.html)
  - `checkDuplicateKey()` 関数：重複チェックロジック
  - `checkAndShowDuplicateWarning()` 関数：警告表示と送信ボタン制御
  - キーフィールドに `oninput` / `onchange` イベント

- [app/templates/application/multi_record_edit.html](../app/templates/application/multi_record_edit.html)
  - 同様の実装

### サーバーサイド（Python）

- [app/routes/application_multi.py](../app/routes/application_multi.py)
  - `submit_multi()` 関数：新規申請の保存時チェック
  - `submit_edit_multi()` 関数：編集申請の保存時チェック

## 使用例

### 申請フィールド定義

```sql
-- ユーザーID（キーフィールド1）
INSERT INTO M_APPLICATION_FIELD (
    field_id, application_type_id, field_code, field_name, field_type,
    is_key_field, is_required_create, display_order
) VALUES (
    SEQ_APPLICATION_FIELD.NEXTVAL, 1, 'user_id', 'ユーザーID', 'text',
    'Y', 'Y', 1
);

-- 所属コード（キーフィールド2）
INSERT INTO M_APPLICATION_FIELD (
    field_id, application_type_id, field_code, field_name, field_type,
    is_key_field, is_required_create, display_order
) VALUES (
    SEQ_APPLICATION_FIELD.NEXTVAL, 1, 'shozoku', '所属コード', 'select',
    'Y', 'Y', 2
);

-- 権限（非キーフィールド）
INSERT INTO M_APPLICATION_FIELD (
    field_id, application_type_id, field_code, field_name, field_type,
    is_key_field, is_required_create, display_order
) VALUES (
    SEQ_APPLICATION_FIELD.NEXTVAL, 1, 'privilege', '権限', 'select',
    'N', 'Y', 3
);
```

### 動作例

| レコード | user_id | shozoku | privilege | 判定 |
|---------|---------|---------|-----------|------|
| 1 | user001 | 1234567 | READ | OK |
| 2 | user001 | 2345678 | WRITE | OK（所属が異なる） |
| 3 | user002 | 1234567 | ADMIN | OK（ユーザーが異なる） |
| 4 | user001 | 1234567 | ADMIN | **NG（レコード1と重複）** |

→ レコード4を追加しようとすると、エラーが表示されます。

## 注意事項

1. **単独でユニークなフィールド**
   - `is_key_field='Y'` が1つだけの場合、そのフィールド単独で重複不可
   - 例：`user_id` のみキーフィールドの場合、同じ `user_id` は2回追加できない

2. **複数フィールドの組み合わせ**
   - `is_key_field='Y'` が複数ある場合、**すべてのキーフィールドの組み合わせ**で重複不可
   - 例：`(user_id, shozoku)` が同じ → 重複
   - 例：`(user_id, shozoku)` の一部だけ同じ → OK

3. **空値の扱い**
   - すべてのキーフィールドが空の場合は重複チェック対象外
   - 一部が空の場合はチェック対象（空文字列として扱われる）

4. **既存レコードのキーフィールド**
   - 既存レコードのキーフィールドは `readonly` で変更不可
   - 新規追加レコードのみ重複チェックの対象

## トラブルシューティング

### 重複チェックが動作しない

**原因1**: `is_key_field='Y'` が設定されていない
```sql
-- 確認方法
SELECT field_id, field_code, field_name, is_key_field
FROM M_APPLICATION_FIELD
WHERE application_type_id = 1;
```

**原因2**: JavaScriptエラーが発生している
- ブラウザの開発者ツール（F12）→ Console タブでエラーを確認

### 送信ボタンが無効化されたままになる

重複を解消しても送信ボタンが有効にならない場合：

1. ブラウザをリロード（Ctrl+F5）
2. キーフィールドの値を少し変更して元に戻す（再チェックをトリガー）

## 将来の拡張

現在は `is_key_field='Y'` のフィールドすべてが対象ですが、将来的に以下の拡張が可能です：

- `unique_group_id` カラムを追加
- 同じ `unique_group_id` を持つフィールドの組み合わせでユニーク制約
- 複数の複合ユニークキーを定義可能（例: `(user_id, shozoku)` と `(email)` の両方）
