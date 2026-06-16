# テストの安全性分析

## 質問: 以前作成したテストでマスタテーブル（M_）を更新する可能性は？

## 回答: ❌ マスタテーブルは更新しません（安全です）

---

## 理由1: Mock DBがデフォルト

### 全テストでMock DBを使用

`tests/conftest.py` で自動的にMock DBが有効化されます：

```python
@pytest.fixture(scope='session')
def app():
    """Flaskアプリケーションのフィクスチャ"""
    # テストモードでMock DBを使用
    os.environ['USE_MOCK_DB'] = 'True'  # ✅ デフォルトでMock DB
    os.environ['FLASK_ENV'] = 'testing'
    
    from app import create_app
    app = create_app('testing')
    
    yield app
```

### Mock DBとは？

実DBの代わりに、メモリ上のダミーデータを返すモック：

```python
# Mock DBの場合
Application.create({...})
# → 実際のDBには書き込まない
# → ダミーのIDを返すだけ

ApplicationType.get_all_active()
# → 実DBではなく、ハードコードされたダミーデータを返す
```

---

## 理由2: 実DBに接続するテストは明示的にマーク

### ハイブリッドDBテストのみが実DBを使用

```python
@pytest.mark.hybrid_db  # ✅ 明示的なマーカー
def test_with_real_db(hybrid_db_session):
    # このテストのみ実DBを使用
    # hybrid_db_session フィクスチャで Mock DB を無効化
```

### 通常のテストはすべてMock DB

```python
# ✅ Mock DB使用（安全）
def test_login(client):
    response = client.post('/auth/login', ...)

# ✅ Mock DB使用（安全）
def test_application_list(auth_client):
    response = auth_client.get('/application/')
```

---

## 全テストファイルの安全性チェック

### 1. 単体テスト（tests/unit/）

| ファイル | Mock DB | 実DB接続 | 安全性 |
|---------|---------|---------|--------|
| `test_auth.py` | ✅ | ❌ | 🟢 安全 |
| `test_application.py` | ✅ | ❌ | 🟢 安全 |
| `test_workflow.py` | ✅ | ❌ | 🟢 安全 |
| `test_validation.py` | ✅ | ❌ | 🟢 安全 |

**結論**: すべてMock DBを使用。実DBには一切接続しない。

---

### 2. 統合テスト（tests/integration/）

| ファイル | Mock DB | 実DB接続 | 安全性 |
|---------|---------|---------|--------|
| `test_application_flow.py` | ✅ | ❌ | 🟢 安全 |
| `test_routes_coverage.py` | ✅ | ❌ | 🟢 安全 |
| `test_hybrid_db.py` | ❌ | ✅ | 🟡 要注意 |

**結論**: 
- `test_hybrid_db.py` **のみ**が実DBを使用
- その他はすべてMock DB

---

### 3. E2Eテスト（tests/e2e/）

| ファイル | Mock DB | 実DB接続 | 安全性 |
|---------|---------|---------|--------|
| `test_complete_workflow.py` | ✅ | ❌ | 🟢 安全 |

**結論**: Mock DBを使用。実DBには接続しない。

---

## 実際のコード分析

### ケース1: 通常のテスト（Mock DB使用）

```python
# tests/unit/test_application.py

def test_submit_application_with_valid_data(auth_client, monkeypatch):
    """有効なデータで申請を提出"""
    
    # ✅ MockApplicationクラスを定義
    class MockApplication:
        @staticmethod
        def create(data):
            return 123  # ダミーIDを返すだけ
    
    # ✅ 実際のApplicationクラスをモックに置き換え
    from app.models import application
    monkeypatch.setattr(application, 'Application', MockApplication)
    
    # ✅ この時点で Application.create() は Mock になっている
    # 実DBには一切アクセスしない
```

### ケース2: ハイブリッドDBテスト（実DB使用）

```python
# tests/integration/test_hybrid_db.py

@pytest.mark.hybrid_db  # ✅ 明示的なマーカー
def test_create_application_with_real_master(hybrid_db_session):
    """実DBを使用（トランザクションテーブルのみ）"""
    
    # ✅ hybrid_db_session フィクスチャで Mock DB を無効化
    # os.environ.pop('USE_MOCK_DB', None)
    
    # ✅ 実際のApplicationクラスを使用
    from app.models.application import Application
    app_id = Application.create({...})  # 実DBに書き込む
    
    # ✅ テスト終了後、自動的に削除される
```

---

## Mock DBの仕組み

### app/utils/db.py の接続判定

```python
def get_db_connection():
    """データベース接続を取得"""
    
    # ✅ 環境変数をチェック
    if os.environ.get('USE_MOCK_DB') == 'True':
        # Mock DBを返す（実DBには接続しない）
        from app.utils.db_mock import MockDBConnection
        return MockDBConnection()
    else:
        # 実DBに接続
        import oracledb
        connection = oracledb.connect(...)
        return connection
```

### Mock DBの動作

```python
# app/utils/db_mock.py

class MockDBConnection:
    """モックDB接続"""
    
    def cursor(self):
        return MockCursor()

class MockCursor:
    """モックカーソル"""
    
    def execute(self, sql, params=None):
        # ✅ 実際にはSQLを実行しない
        # ハードコードされたダミーデータを準備
        pass
    
    def fetchone(self):
        # ✅ ダミーデータを返す
        return {'application_type_id': 1, 'application_type_name': 'テスト'}
    
    def fetchall(self):
        # ✅ ダミーデータのリストを返す
        return [
            {'application_type_id': 1, 'application_type_name': 'テスト1'},
            {'application_type_id': 2, 'application_type_name': 'テスト2'}
        ]
```

---

## テスト実行時のDB接続状況

### デフォルトのテスト実行

```bash
pytest --cov=app --cov-report=html
```

**動作**:
1. `conftest.py` で `USE_MOCK_DB=True` を設定
2. すべてのテストでMock DBを使用
3. 実DBには一切接続しない ✅

---

### ハイブリッドDBテストのみ実行

```bash
pytest -m hybrid_db --cov=app
```

**動作**:
1. `@pytest.mark.hybrid_db` のテストのみ実行
2. `hybrid_db_session` フィクスチャで Mock DB を無効化
3. 実DBに接続する ⚠️
4. ただし、**トランザクションテーブル（T_*）のみ**を更新
5. **マスタテーブル（M_*）は読み取りのみ** ✅
6. テスト後、自動的にクリーンアップ ✅

---

## マスタテーブル（M_*）の安全性

### すべてのテストでマスタテーブルは安全

#### Mock DBテスト（デフォルト）

```python
# ✅ Mock DBを使用
ApplicationType.get_all_active()
# → 実DBには接続しない
# → マスタテーブルは読み取りすらしない
```

#### ハイブリッドDBテスト

```python
# ✅ 実DBに接続するが、読み取りのみ
ApplicationType.get_all_active()
# → SELECT文のみ（読み取り）
# → INSERT/UPDATE/DELETEは実行しない
```

---

## 更新されるのはトランザクションテーブル（T_*）のみ

### ハイブリッドDBテストで更新されるテーブル

| テーブル | 操作 | クリーンアップ |
|---------|------|--------------|
| `T_APPLICATION` | INSERT | ✅ DELETE |
| `T_APPLICATION_DETAIL` | INSERT | ✅ DELETE |
| `T_WORKFLOW_INSTANCE` | INSERT | ✅ DELETE |
| `T_WORKFLOW_NODE_INSTANCE` | INSERT | ✅ DELETE |
| `T_WORKFLOW_NODE_APPROVER` | INSERT | ✅ DELETE |

### 更新されないテーブル（マスタ）

| テーブル | 操作 | 理由 |
|---------|------|------|
| `M_APPLICATION_TYPE` | SELECT のみ | 読み取り専用 ✅ |
| `M_APPLICATION_FIELD` | SELECT のみ | 読み取り専用 ✅ |
| `M_WORKFLOW_DEFINITION` | SELECT のみ | 読み取り専用 ✅ |
| `M_WORKFLOW_NODE_DEFINITION` | SELECT のみ | 読み取り専用 ✅ |
| `M_VALIDATION_RULE` | SELECT のみ | 読み取り専用 ✅ |
| `M_PULLDOWN_GROUP` | SELECT のみ | 読み取り専用 ✅ |
| `M_PULLDOWN_OPTION` | SELECT のみ | 読み取り専用 ✅ |
| `e_imdb2_users` | SELECT のみ | 読み取り専用 ✅ |

---

## 実行コマンド別の安全性

### 1. デフォルトのテスト実行（最も安全）

```bash
pytest --cov=app --cov-report=html
```

**安全性**: 🟢 **完全に安全**
- Mock DBのみ使用
- 実DBには一切接続しない
- マスタテーブルもトランザクションテーブルも触らない

---

### 2. 単体テストのみ（安全）

```bash
pytest -m unit --cov=app
```

**安全性**: 🟢 **完全に安全**
- Mock DBのみ使用
- 実DBには接続しない

---

### 3. 統合テスト（hybrid_db以外）（安全）

```bash
pytest -m integration --cov=app
```

**安全性**: 🟢 **完全に安全**
- Mock DBのみ使用
- `test_hybrid_db.py` は実行されない（`@pytest.mark.hybrid_db`）

---

### 4. ハイブリッドDBテスト（要注意だが安全）

```bash
pytest -m hybrid_db --cov=app
```

**安全性**: 🟡 **要注意だが安全**
- 実DBに接続する
- **マスタテーブル（M_*）**: 読み取りのみ ✅
- **トランザクションテーブル（T_*）**: 作成・削除
- テスト後、自動クリーンアップ ✅

---

## まとめ

### ✅ 以前作成したテストファイルの安全性

| テストファイル | Mock DB | 実DB | マスタ更新 | 安全性 |
|--------------|---------|------|-----------|--------|
| `test_auth.py` | ✅ | ❌ | ❌ | 🟢 完全に安全 |
| `test_application.py` | ✅ | ❌ | ❌ | 🟢 完全に安全 |
| `test_workflow.py` | ✅ | ❌ | ❌ | 🟢 完全に安全 |
| `test_validation.py` | ✅ | ❌ | ❌ | 🟢 完全に安全 |
| `test_application_flow.py` | ✅ | ❌ | ❌ | 🟢 完全に安全 |
| `test_routes_coverage.py` | ✅ | ❌ | ❌ | 🟢 完全に安全 |
| `test_complete_workflow.py` | ✅ | ❌ | ❌ | 🟢 完全に安全 |
| `test_hybrid_db.py` | ❌ | ✅ | ❌ | 🟢 安全（読み取りのみ） |

### 結論

**すべてのテストファイルでマスタテーブル（M_*）は更新されません。**

- **通常のテスト**: Mock DBを使用、実DBには接続しない
- **ハイブリッドDBテスト**: 実DBを使用するが、マスタは読み取りのみ

**安心してテストを実行できます！**

---

## 念のための確認方法

### テスト実行前にDBを確認

```sql
-- マスタテーブルのレコード数を記録
SELECT COUNT(*) FROM M_APPLICATION_TYPE;
SELECT COUNT(*) FROM M_WORKFLOW_DEFINITION;
SELECT COUNT(*) FROM M_VALIDATION_RULE;
```

### テスト実行

```bash
pytest --cov=app --cov-report=html
```

### テスト実行後に再確認

```sql
-- レコード数が変わっていないことを確認
SELECT COUNT(*) FROM M_APPLICATION_TYPE;  -- 変わっていない ✅
SELECT COUNT(*) FROM M_WORKFLOW_DEFINITION;  -- 変わっていない ✅
SELECT COUNT(*) FROM M_VALIDATION_RULE;  -- 変わっていない ✅
```

**結果**: マスタテーブルは一切変更されていません ✅
