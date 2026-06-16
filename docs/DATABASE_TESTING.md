# データベーステストの安全な実施方法

## ⚠️ 警告: 実DBテストのリスク

実DBを使ったテストは以下のリスクがあります：

### 危険性

1. **データの汚染** - テストデータが本番/開発DBに残る
2. **データの削除** - 既存の重要なデータを誤って削除
3. **データの更新** - 既存データを意図せず変更
4. **テストの失敗で不完全なデータが残る**

### ❌ やってはいけないこと

```python
# ❌ 本番DBに直接書き込むテスト
def test_create_application():
    app_id = Application.create({...})  # 本番DBに登録される！
    assert app_id > 0
    # データが残ったまま...
```

---

## ✅ 安全なテスト方法

### 方法1: Mock DBを使う（推奨・現在の方法）

**メリット**:
- ✅ 実DBを汚染しない
- ✅ 高速
- ✅ DBサーバー不要

**デメリット**:
- ⚠️ 実際のDB動作とは異なる可能性
- ⚠️ SQL文法チェックができない

```python
# ✅ Mock DBを使用（安全）
import os
os.environ['USE_MOCK_DB'] = 'True'

from app.models.application_type import ApplicationType
app_types = ApplicationType.get_all_active()
# Mock DBから取得（実DBは触らない）
```

---

### 方法2: テスト専用DBを使う（推奨）

**環境分離**: 本番/開発DBとは別のテスト専用DBを用意

#### 2-1. テスト用DB接続設定

`.env.test` ファイルを作成：

```env
# .env.test（テスト専用DB）
ORACLE_DSN=testdb_hostname:1521/TESTDB
ORACLE_USER=test_user
ORACLE_PASSWORD=test_password

# テスト実行前に必ず確認！
# このDBはテスト用で、データが削除されてもOKなDB
```

#### 2-2. pytest設定で自動切り替え

`conftest.py` を修正：

```python
import os
import pytest

@pytest.fixture(scope='session')
def setup_test_db():
    """テスト開始時にテスト用DB接続に切り替え"""
    # .env.testを読み込む
    from dotenv import load_dotenv
    load_dotenv('.env.test', override=True)
    
    # テスト用DBであることを確認
    dsn = os.environ.get('ORACLE_DSN')
    if 'testdb' not in dsn.lower() and 'test' not in dsn.lower():
        pytest.exit("⚠️ TEST DB SAFETY CHECK FAILED: DSN does not contain 'test'")
    
    print(f"✅ Using TEST DB: {dsn}")
    yield
```

---

### 方法3: トランザクションロールバック（高度）

**原理**: テスト後に変更を取り消す

#### 3-1. フィクスチャでロールバック

```python
import pytest
from app.utils.db import get_db_connection

@pytest.fixture(scope='function')
def db_transaction(setup_test_db):
    """テスト用DBトランザクション（自動ロールバック）"""
    conn = get_db_connection()
    
    # トランザクション開始
    cursor = conn.cursor()
    cursor.execute("SAVEPOINT test_savepoint")
    
    yield conn
    
    # テスト終了後、必ずロールバック
    try:
        cursor.execute("ROLLBACK TO SAVEPOINT test_savepoint")
        conn.commit()
    finally:
        conn.close()


@pytest.mark.db
def test_create_with_rollback(db_transaction):
    """テスト後に自動ロールバック"""
    from app.models.application import Application
    
    # データを作成
    app_id = Application.create({...})
    assert app_id > 0
    
    # テスト終了後、自動的にロールバックされる
    # → DBには残らない ✅
```

#### 3-2. 注意点

⚠️ **ロールバックの制限**:
- DDL文（CREATE TABLE等）はロールバックできない
- 別トランザクションで実行されたCOMMITは取り消せない
- AUTO_COMMITが有効だとロールバックできない

---

### 方法4: データクリーンアップ（セットアップ/ティアダウン）

**原理**: テスト前にデータ準備、テスト後にクリーンアップ

```python
import pytest
from app.models.application import Application

@pytest.fixture(scope='function')
def test_application(db_transaction):
    """テストデータを作成し、終了後に削除"""
    # セットアップ: テストデータ作成
    app_id = Application.create({
        'application_type_id': 1,
        'applicant_user_id': 'test_user_cleanup',
        'application_title': 'テスト用申請（削除予定）',
        # ...
    })
    
    yield app_id
    
    # ティアダウン: テストデータ削除
    try:
        Application.delete(app_id)
    except Exception as e:
        print(f"⚠️ クリーンアップ失敗: {e}")


@pytest.mark.db
def test_with_cleanup(test_application):
    """テストデータは自動的に削除される"""
    app = Application.get_by_id(test_application)
    assert app is not None
    # テスト終了後、自動削除される
```

---

## 推奨アプローチ

### レベル1: Mock DB（現在の方法）✅

**対象**: ほとんどのテスト

```bash
# デフォルトでMock DB使用
pytest --cov=app --cov-report=html
```

**利点**:
- 安全（実DBを触らない）
- 高速
- 環境依存なし

### レベル2: テスト専用DB + ロールバック

**対象**: 重要なロジックの検証

```python
@pytest.mark.db
@pytest.mark.slow
def test_complex_workflow_with_real_db(db_transaction):
    """実DBで複雑なワークフローをテスト（ロールバック付き）"""
    # 実際のDB動作を検証
    # テスト後は自動ロールバック
```

**実行方法**:
```bash
# テスト専用DBマーカーのみ実行
pytest -m db --cov=app

# または手動で実行
pytest tests/integration/test_db_integration.py
```

### レベル3: 手動テスト（本番環境想定）

**対象**: リリース前の最終確認

```bash
# 手動でテスト環境DBに対して実行
# テスト後は手動でデータ確認・削除
```

---

## テスト用DBの準備

### 手順1: テスト専用スキーマを作成

```sql
-- Oracle DBの場合
CREATE USER test_nam_task IDENTIFIED BY test_password;
GRANT CONNECT, RESOURCE TO test_nam_task;

-- 本番と同じテーブル構造をコピー
-- （データは空またはテスト用サンプルデータのみ）
```

### 手順2: テスト用接続情報を設定

```env
# .env.test
ORACLE_DSN=testserver:1521/TESTDB
ORACLE_USER=test_nam_task
ORACLE_PASSWORD=test_password
```

### 手順3: テスト実行時に確認

```python
# conftest.py
def pytest_configure(config):
    """テスト開始前の安全チェック"""
    if config.option.markexpr and 'db' in config.option.markexpr:
        dsn = os.environ.get('ORACLE_DSN', '')
        if 'production' in dsn.lower() or 'prod' in dsn.lower():
            pytest.exit("⚠️ DANGER: Cannot run DB tests against production!")
```

---

## 実行コマンド

### Mock DBテスト（安全・デフォルト）

```bash
# 環境変数で明示的にMock DBを指定
set USE_MOCK_DB=True
pytest --cov=app --cov-report=html
```

### テスト専用DBテスト（安全）

```bash
# .env.testを使用
pytest -m db --cov=app --cov-report=html
```

### 実行前の確認事項

✅ **実行前チェックリスト**:
1. テスト専用DBに接続していることを確認
2. 本番DBではないことを確認
3. データがクリーンアップされることを確認
4. バックアップがあることを確認（念のため）

---

## サンプル: 安全なDB統合テスト

```python
"""
安全なDB統合テスト
- テスト専用DB使用
- トランザクションロールバック
- データクリーンアップ
"""
import pytest


@pytest.fixture(scope='module')
def verify_test_db():
    """テスト用DBであることを確認"""
    import os
    dsn = os.environ.get('ORACLE_DSN', '')
    
    # 安全チェック
    if not any(keyword in dsn.lower() for keyword in ['test', 'dev', 'development']):
        pytest.skip("⚠️ Not a test database - skipping DB tests")
    
    print(f"✅ Verified TEST DB: {dsn}")


@pytest.mark.db
@pytest.mark.slow
class TestApplicationWithRealDB:
    """実DBを使った統合テスト（安全）"""
    
    def test_application_type_query(self, verify_test_db, db_transaction):
        """申請種類の取得（読み取りのみ・安全）"""
        from app.models.application_type import ApplicationType
        
        # Mock DBを無効化
        import os
        os.environ.pop('USE_MOCK_DB', None)
        
        # 実DBから取得（読み取りのみなので安全）
        app_types = ApplicationType.get_all_active()
        
        assert isinstance(app_types, list)
        # データが存在する場合の検証
        if len(app_types) > 0:
            assert 'application_type_id' in app_types[0]
    
    def test_application_create_and_rollback(self, verify_test_db, db_transaction):
        """申請作成とロールバック"""
        from app.models.application import Application
        
        import os
        os.environ.pop('USE_MOCK_DB', None)
        
        # データ作成
        app_id = Application.create({
            'application_type_id': 1,
            'action_type': 'create',
            'applicant_user_id': 'test_rollback_user',
            'applicant_shozoku': '9999999',
            'application_title': 'ロールバックテスト',
            'remarks': 'このデータは自動削除されます'
        })
        
        assert app_id is not None
        
        # 作成されたことを確認
        app = Application.get_by_id(app_id)
        assert app is not None
        assert app['application_title'] == 'ロールバックテスト'
        
        # テスト終了後、db_transactionフィクスチャが自動ロールバック
```

---

## まとめ

### ✅ 推奨: Mock DBを使う

```python
# デフォルトの安全な方法
pytest --cov=app --cov-report=html
```

**理由**:
- 実DBを汚染しない
- 高速
- 環境構築不要

### 🟡 必要に応じて: テスト専用DB + ロールバック

```python
# テスト専用DBで実行（ロールバック付き）
pytest -m db --cov=app
```

**理由**:
- 実際のDB動作を検証
- 安全にテストできる

### ❌ 避けるべき: 本番/開発DBへの直接書き込み

```python
# これは絶対にやらない！
# 本番DBにテストデータが残る
```

---

## 結論

**質問の答え**: はい、実DBを使ったテストはDBを更新してしまいます。

**対策**:
1. **Mock DBを使う**（現在の方法、推奨）
2. **テスト専用DBを用意する**
3. **トランザクションロールバックを使う**
4. **データクリーンアップを実装する**

**現在のプロジェクトでは、Mock DBで十分です。**
実DBテストは、本番リリース前の最終確認時に、テスト専用DBを用意してから実施することを推奨します。
