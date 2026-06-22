# テストデータの設定ガイド

## 概要

このドキュメントでは、実際に存在するユーザーや所属でテストするために、テストデータを変更する方法を説明します。

---

## テストデータが定義されている場所

### 1. **共通フィクスチャ（最重要）**

#### A. `tests/conftest_hybrid_db.py`

**場所**: 10-11行目

```python
# ✏️ ここを変更
TEST_SHOZOKU = '9999999'  # テスト用所属コード
TEST_USER_PREFIX = 'test_hybrid_'  # テストユーザーIDのプレフィックス
```

**変更例**:
```python
# 実際に存在する所属とユーザーを使用
TEST_SHOZOKU = '1230000'  # システム企画室の所属コード
TEST_USER_PREFIX = 'your_actual_user_id'  # 実際のユーザーID
```

**影響範囲**: ハイブリッドDBテスト全体

---

#### B. `tests/conftest.py`

**場所1**: 43-46行目（一般ユーザー）

```python
@pytest.fixture(scope='function')
def auth_client(client):
    """認証済みテストクライアント"""
    with client.session_transaction() as sess:
        # ✏️ ここを変更
        sess['user_id'] = 'test_user'
        sess['user_name'] = 'テストユーザー'
        sess['shozoku'] = '1234000'
        sess['shozoku_name'] = 'テスト部署'
        sess['is_admin'] = False
    yield client
```

**変更例**:
```python
sess['user_id'] = 'your_user_id'  # 実際のユーザーID
sess['user_name'] = '山田太郎'  # 実際のユーザー名
sess['shozoku'] = '1234000'  # 実際の所属コード
sess['shozoku_name'] = '営業部'  # 実際の所属名
```

**場所2**: 55-58行目（管理者ユーザー）

```python
@pytest.fixture(scope='function')
def admin_client(client):
    """管理者権限の認証済みテストクライアント"""
    with client.session_transaction() as sess:
        # ✏️ ここを変更
        sess['user_id'] = 'admin_user'
        sess['user_name'] = '管理者ユーザー'
        sess['shozoku'] = '1234000'
        sess['shozoku_name'] = 'システム企画室'
        sess['is_admin'] = True
    yield client
```

**変更例**:
```python
sess['user_id'] = 'admin_real_id'  # 実際の管理者ID
sess['user_name'] = '管理者 太郎'  # 実際の管理者名
sess['shozoku'] = '1230000'  # システム企画室の実際の所属コード
sess['shozoku_name'] = 'システム企画室'
```

**場所3**: 69-70行目（サンプル申請データ）

```python
@pytest.fixture(scope='function')
def sample_application_data():
    """サンプル申請データ"""
    return {
        'application_type_id': 1,
        'action_type': 'create',
        # ✏️ ここを変更
        'applicant_user_id': 'test_user',
        'applicant_shozoku': '1234000',
        'jurisdiction_shozoku': '1234000',
        'application_title': 'テスト申請',
        'remarks': '回帰テスト用データ'
    }
```

**変更例**:
```python
'applicant_user_id': 'your_user_id',
'applicant_shozoku': '1234000',
'jurisdiction_shozoku': '1234000',
```

---

### 2. **ハイブリッドDBテスト用フィクスチャ**

#### `tests/conftest_hybrid_db.py`

**場所**: 171-174行目

```python
@pytest.fixture(scope='function')
def test_application_data():
    """テスト用申請データのテンプレート"""
    return {
        'application_type_id': 1,
        'action_type': 'create',
        # ✏️ ここを変更
        'applicant_user_id': f'{TEST_USER_PREFIX}001',
        'applicant_shozoku': TEST_SHOZOKU,
        'jurisdiction_shozoku': TEST_SHOZOKU,
        'application_title': '[TEST] ハイブリッドDBテスト',
        'remarks': 'このデータは自動削除されます'
    }
```

**変更方法**: 
- `TEST_SHOZOKU`と`TEST_USER_PREFIX`を変更すれば自動的に反映される

---

### 3. **固定テストデータ**

#### `tests/fixtures/test_data.py`

**場所**: 8-30行目

```python
# ユーザーデータ
USERS = {
    'applicant': {
        # ✏️ ここを変更
        'user_id': 'test_applicant',
        'user_name': '申請者テスト',
        'shozoku': '1234000',
        'shozoku_name': 'テスト部署'
    },
    'approver1': {
        'user_id': 'test_approver1',
        'user_name': '承認者1',
        'shozoku': '1234000',
        'shozoku_name': 'テスト部署'
    },
    'approver2': {
        'user_id': 'test_approver2',
        'user_name': '承認者2（システム企画室）',
        'shozoku': '1230000',
        'shozoku_name': 'システム企画室'
    },
    'admin': {
        'user_id': 'test_admin',
        'user_name': '管理者',
        'shozoku': '1230000',
        'shozoku_name': 'システム企画室'
    }
}
```

**変更例**:
```python
USERS = {
    'applicant': {
        'user_id': 'yamada_taro',  # 実際のユーザーID
        'user_name': '山田太郎',
        'shozoku': '1234000',  # 実際の所属コード
        'shozoku_name': '営業部'
    },
    # ...
}
```

---

## 推奨される設定方法

### 方法1: 環境変数で設定（推奨）

テストデータを環境変数で制御できるようにします。

#### `tests/conftest_hybrid_db.py` を修正

```python
import os

# ✅ 環境変数から読み込む
TEST_SHOZOKU = os.environ.get('TEST_SHOZOKU', '9999999')
TEST_USER_PREFIX = os.environ.get('TEST_USER_PREFIX', 'test_hybrid_')
```

#### 実行時に環境変数を設定

```bash
# Windows
set TEST_SHOZOKU=1234000
set TEST_USER_PREFIX=your_user_id
pytest -m hybrid_db --cov=app -v

# Linux/Mac
export TEST_SHOZOKU=1234000
export TEST_USER_PREFIX=your_user_id
pytest -m hybrid_db --cov=app -v
```

---

### 方法2: 設定ファイルで管理（推奨）

テスト用の設定ファイルを作成します。

#### `tests/test_config.py` を作成

```python
"""
テストデータ設定
実際に存在するユーザーや所属を設定してください
"""

# ハイブリッドDBテスト用
TEST_SHOZOKU = '1234000'  # 実際の所属コード
TEST_USER_PREFIX = 'your_actual_user_id'  # 実際のユーザーID

# Mock DBテスト用
MOCK_USER_ID = 'your_user_id'
MOCK_USER_NAME = '山田太郎'
MOCK_SHOZOKU = '1234000'
MOCK_SHOZOKU_NAME = '営業部'

# 管理者用
ADMIN_USER_ID = 'admin_id'
ADMIN_USER_NAME = '管理者 太郎'
ADMIN_SHOZOKU = '1230000'
ADMIN_SHOZOKU_NAME = 'システム企画室'
```

#### `tests/conftest_hybrid_db.py` を修正

```python
# 設定ファイルから読み込む
try:
    from tests.test_config import TEST_SHOZOKU, TEST_USER_PREFIX
except ImportError:
    # 設定ファイルがない場合はデフォルト値
    TEST_SHOZOKU = '9999999'
    TEST_USER_PREFIX = 'test_hybrid_'
```

---

### 方法3: 直接編集（シンプル）

各ファイルを直接編集します。

#### 必須の変更箇所

1. **`tests/conftest_hybrid_db.py:10-11`**
   ```python
   TEST_SHOZOKU = '1234000'  # ← 実際の所属コード
   TEST_USER_PREFIX = 'your_user_id'  # ← 実際のユーザーID
   ```

2. **`tests/conftest.py:43-46`**
   ```python
   sess['user_id'] = 'your_user_id'
   sess['shozoku'] = '1234000'
   ```

3. **`tests/conftest.py:55-58`**
   ```python
   sess['user_id'] = 'admin_user_id'
   sess['shozoku'] = '1230000'
   ```

---

## 実際の使用例

### ケース1: 営業部のユーザーでテスト

```python
# tests/conftest_hybrid_db.py
TEST_SHOZOKU = '1234000'  # 営業部
TEST_USER_PREFIX = 'yamada_taro'  # 営業部の山田太郎さん
```

### ケース2: システム企画室のユーザーでテスト

```python
# tests/conftest_hybrid_db.py
TEST_SHOZOKU = '1230000'  # システム企画室
TEST_USER_PREFIX = 'tanaka_hanako'  # システム企画室の田中花子さん
```

### ケース3: 複数の所属でテスト

```python
# tests/conftest_hybrid_db.py
TEST_SHOZOKU_APPLICANT = '1234000'  # 申請者所属
TEST_SHOZOKU_JURISDICTION = '5678000'  # 所管所属
TEST_USER_PREFIX = 'your_user_id'
```

---

## 注意事項

### ✅ 安全な設定

1. **実際のユーザーIDを使用**
   - DBに存在するユーザーIDを設定
   - `e_imdb2_users`テーブルで確認

2. **実際の所属コードを使用**
   - DBに存在する所属コードを設定
   - `e_imdb2_users`テーブルで確認

3. **テストデータの識別**
   - 申請タイトルに`[TEST]`プレフィックスを付ける
   - クリーンアップで削除しやすくする

### ⚠️ 注意すべき点

1. **本番データの参照**
   - マスタデータ（M_*）は実際のデータを参照する
   - 訂正・削除申請では既存の申請データを参照する

2. **トランザクションデータの作成**
   - 申請データ（T_APPLICATION）は新規作成される
   - テスト後に自動削除される

3. **ユーザー権限**
   - 設定したユーザーIDが実際に申請権限を持っているか確認
   - 所属が申請種類の制限に該当しないか確認

---

## クリーンアップの確認

### テスト実行後の確認SQL

```sql
-- テストデータが残っていないか確認
SELECT application_id, application_title, applicant_user_id, applicant_shozoku
FROM T_APPLICATION
WHERE application_title LIKE '[TEST]%'
   OR applicant_user_id LIKE 'test_%';
-- 0件であることを確認（クリーンアップ成功）
```

### 手動でクリーンアップ

```sql
-- テストデータを手動削除（必要な場合）
DELETE FROM T_WORKFLOW_NODE_APPROVER 
WHERE node_instance_id IN (
    SELECT node_instance_id FROM T_WORKFLOW_NODE_INSTANCE
    WHERE workflow_instance_id IN (
        SELECT workflow_instance_id FROM T_WORKFLOW_INSTANCE
        WHERE application_id IN (
            SELECT application_id FROM T_APPLICATION
            WHERE application_title LIKE '[TEST]%'
        )
    )
);

DELETE FROM T_WORKFLOW_NODE_INSTANCE 
WHERE workflow_instance_id IN (
    SELECT workflow_instance_id FROM T_WORKFLOW_INSTANCE
    WHERE application_id IN (
        SELECT application_id FROM T_APPLICATION
        WHERE application_title LIKE '[TEST]%'
    )
);

DELETE FROM T_WORKFLOW_INSTANCE 
WHERE application_id IN (
    SELECT application_id FROM T_APPLICATION
    WHERE application_title LIKE '[TEST]%'
);

DELETE FROM T_APPLICATION_DETAIL 
WHERE application_id IN (
    SELECT application_id FROM T_APPLICATION
    WHERE application_title LIKE '[TEST]%'
);

DELETE FROM T_APPLICATION 
WHERE application_title LIKE '[TEST]%';

COMMIT;
```

---

## まとめ

### 最も簡単な変更方法

**1つのファイルを編集するだけ**:

`tests/conftest_hybrid_db.py` の10-11行目を変更：

```python
TEST_SHOZOKU = '1234000'  # ← 実際の所属コード
TEST_USER_PREFIX = 'your_user_id'  # ← 実際のユーザーID
```

これだけで、ハイブリッドDBテスト全体が実際のユーザー・所属でテストされます。

### 実行確認

```bash
# テストデータ設定を確認
python -c "from tests.conftest_hybrid_db import TEST_SHOZOKU, TEST_USER_PREFIX; print(f'所属: {TEST_SHOZOKU}, ユーザー: {TEST_USER_PREFIX}')"

# テスト実行
pytest -m hybrid_db --cov=app -v -s
```

これで、実際に存在する本番データを参照しながら、安全にテストできます！
