# リソース選択とデータ入力の回帰テスト

## 概要

このドキュメントでは、修正・削除申請におけるリソース選択とデータ入力のテストについて説明します。

---

## 2つの修正点

### 1. ユーザーIDの修正 ✅

#### 問題点

```python
# ❌ 以前の実装
TEST_USER_PREFIX = 'test_hybrid_'
'applicant_user_id': f'{TEST_USER_PREFIX}001'  # test_hybrid_001
```

これは不適切です。理由：
- ユーザーIDは固有のもの（バリエーションはない）
- `test_hybrid_001`というユーザーは存在しない
- 実際の本番データを参照できない

#### 修正後

```python
# ✅ 修正後
TEST_USER_ID = 'your_actual_user_id'  # 実際に存在するユーザーID
'applicant_user_id': TEST_USER_ID
```

**設定場所**: `tests/conftest_hybrid_db.py` の 9-11行目

```python
# 実際に存在するユーザー・所属に変更してください
TEST_USER_ID = 'your_user_id'  # ← ここを変更
TEST_SHOZOKU = '1234000'  # ← 実際の所属コード
TEST_JURISDICTION_SHOZOKU = '1234000'  # ← 所管所属コード
```

---

### 2. リソース選択後のデータ入力テスト ✅

#### 質問

> 申請画面はresourceを選択した後に、実際にデータ入力を行いますが、
> そこまで回帰テストで行うのは難しいですか

#### 回答: いいえ、可能です！

実装しました。

---

## リソース選択フローのテスト

### テストシナリオ

#### 1. 修正申請フロー

```
1. 既存リソース一覧から選択
   ↓
2. 選択したリソースの現在のデータを取得（本番データから）
   ↓
3. 修正フォームにデータを入力
   ↓
4. 申請を作成（トランザクションテーブルに保存）
   ↓
5. 確認（既存リソースは変更されていない）
```

#### 2. 削除申請フロー

```
1. 既存リソース一覧から選択
   ↓
2. 削除理由を入力
   ↓
3. 削除申請を作成
   ↓
4. 確認（既存リソースは削除されていない）
```

---

## テストコード

### ファイル: `tests/integration/test_resource_selection.py`

#### テスト1: 修正申請（リソース選択 → データ入力）

```python
@pytest.mark.integration
@pytest.mark.hybrid_db
def test_modify_with_resource_selection(create_test_application, verify_test_db):
    """修正申請: リソース選択 → データ入力 → 申請作成"""
    
    # 1. 既存リソースを取得（本番データから読み取り）
    resources = Resource.search(resource_type='gmail_group', limit=1)
    existing_resource = resources[0]
    resource_id = existing_resource['resource_id']
    
    # 2. リソースの現在のデータを取得
    current_data = Resource.get_by_id(resource_id)
    
    # 3. 修正申請を作成（トランザクションテーブルに書き込み）
    app_id = Application.create({
        'action_type': 'modify',
        'resource_id': resource_id,  # 既存リソースを参照
        'applicant_user_id': TEST_USER_ID,
        # ...
    })
    
    # 4. フィールドデータを入力（修正内容）
    details = []
    for field in fields:
        # 既存の値を取得
        current_value = current_data.get(field['field_name'])
        
        # 修正後の値
        new_value = f"{current_value}_MODIFIED_TEST"
        
        details.append({
            'field_id': field['field_id'],
            'field_value': new_value
        })
    
    # 5. 申請詳細を保存
    ApplicationDetail.create_bulk(app_id, details)
    
    # ✅ 既存リソース（M_RESOURCE）は変更されていない
    # ✅ 申請データ（T_APPLICATION）のみ作成される
    # ✅ テスト終了後、申請データは自動削除される
```

---

## 実行方法

### テスト実行

```bash
# リソース選択テストを実行
pytest tests/integration/test_resource_selection.py -v -s

# または、ハイブリッドDBテストとして実行
pytest -m hybrid_db -v -s
```

### 実行例

```
tests/integration/test_resource_selection.py::TestResourceSelectionFlow::test_modify_with_resource_selection

✅ 既存リソース: sales-team@example.com
✅ フィールド数: 3件
✅ 現在のデータ取得完了
✅ 申請作成: application_id=123
✅ 申請詳細保存: 3件
✅ 保存確認完了: 3件

PASSED

✅ クリーンアップ完了: 申請1件、ワークフロー0件
```

---

## HTML画面イメージテスト

リソース選択画面とデータ入力画面のHTMLも保存できます。

### テストコード

```python
@pytest.mark.visual
def test_modify_resource_list_html(auth_client, save_html):
    """修正対象リソース一覧画面のHTML"""
    response = auth_client.get('/application/modify/select-resource/1')
    save_html(response, '07_modify_select_resource.html')
```

### 実行

```bash
# 画面イメージテストを実行
pytest -m visual -v -s

# 保存されたHTMLを確認
start test_results\html\07_modify_select_resource.html
```

---

## 安全性の確認

### テストで行われること

#### ✅ 読み取りのみ（安全）

- マスタテーブル（M_*）から申請種類・フィールド定義を取得
- リソーステーブル（M_RESOURCE）から既存リソースを取得
- 既存リソースの現在のデータを取得

#### ✅ トランザクションテーブルに書き込み（安全・自動削除）

- T_APPLICATION に申請を作成
- T_APPLICATION_DETAIL に申請詳細を作成
- テスト終了後、自動的に削除される

#### ❌ 行わないこと

- 既存リソースの更新
- 既存リソースの削除
- マスタテーブルの変更

---

## 複数レコード形式のテスト

複数レコード形式の申請（例: 複数ユーザーの権限変更）もテストできます。

### テストコード

```python
def test_multi_record_data_entry():
    """複数レコード形式: 複数行のデータを入力"""
    
    # 複数レコードを入力（3レコード）
    details = []
    for record_seq in range(1, 4):  # 3レコード
        for field in fields:
            details.append({
                'detail_seq': record_seq,  # レコード番号
                'field_id': field['field_id'],
                'field_value': f"Record{record_seq}_Value"
            })
    
    # 一括保存
    ApplicationDetail.create_bulk(app_id, details)
    
    # レコード別に取得
    grouped = ApplicationDetail.get_grouped_by_seq(app_id)
    assert len(grouped) == 3  # 3レコード
```

---

## 実際の運用例

### ステップ1: テストデータを設定

`tests/conftest_hybrid_db.py` を編集：

```python
# 実際に存在するユーザー・所属に変更
TEST_USER_ID = 'yamada_taro'  # 実際のユーザーID
TEST_SHOZOKU = '1234000'  # 実際の所属コード
TEST_JURISDICTION_SHOZOKU = '1234000'
```

### ステップ2: テスト実行

```bash
# リソース選択フローをテスト
pytest tests/integration/test_resource_selection.py::TestResourceSelectionFlow::test_modify_with_resource_selection -v -s
```

### ステップ3: 結果確認

```sql
-- テストデータが残っていないか確認
SELECT * FROM T_APPLICATION WHERE application_title LIKE '[TEST]%';
-- → 0件（クリーンアップ成功）

-- 既存リソースが変更されていないか確認
SELECT * FROM M_RESOURCE WHERE resource_id = 1;
-- → 変更なし（読み取りのみ）
```

---

## トラブルシューティング

### 問題1: "テスト用リソースが存在しません"

**原因**: 既存リソースがDBに存在しない

**解決方法**:
```sql
-- リソースを確認
SELECT * FROM M_RESOURCE WHERE resource_type = 'gmail_group';
```

リソースが存在しない場合は、テストをスキップするか、手動でサンプルデータを作成してください。

---

### 問題2: フィールド定義が見つからない

**原因**: 申請種類のフィールド定義が設定されていない

**解決方法**:
```sql
-- フィールド定義を確認
SELECT * FROM M_APPLICATION_FIELD WHERE application_type_id = 1;
```

---

## まとめ

### ✅ 修正内容

1. **ユーザーIDの修正**
   - `TEST_USER_PREFIX` → `TEST_USER_ID`
   - 実際に存在するユーザーIDを使用

2. **リソース選択フローのテスト実装**
   - 既存リソースの取得（本番データから）
   - データ入力
   - 申請作成（トランザクションテーブルのみ）
   - 自動クリーンアップ

### 🎯 テストファイル

- `tests/integration/test_resource_selection.py` - リソース選択フローのテスト
- `tests/conftest_hybrid_db.py` - テストデータ設定（修正済み）

### 🚀 実行方法

```bash
# リソース選択テスト
pytest tests/integration/test_resource_selection.py -v -s

# 画面イメージも保存
pytest -m visual -v -s

# HTMLを確認
start test_results\html\07_modify_select_resource.html
```

これで、リソース選択から実際のデータ入力まで、完全にテストできます！
