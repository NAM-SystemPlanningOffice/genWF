# テストガイド

このドキュメントは、genWFシステムの回帰テストの実行方法とテスト構成について説明します。

## 目次

1. [テスト環境のセットアップ](#テスト環境のセットアップ)
2. [テストの実行方法](#テストの実行方法)
3. [テスト構成](#テスト構成)
4. [テストカテゴリー](#テストカテゴリー)
5. [テストデータ](#テストデータ)
6. [カバレッジレポート](#カバレッジレポート)
7. [トラブルシューティング](#トラブルシューティング)

---

## テスト環境のセットアップ

### 必要な依存パッケージのインストール

```bash
# 仮想環境を有効化
venv\Scripts\activate  # Windows
# または
source venv/bin/activate  # Linux/Mac

# テスト用パッケージをインストール
pip install pytest pytest-cov pytest-mock
```

### 環境変数の設定

テスト実行時は自動的にMock DBモードが有効になります。
実DBを使用する統合テストを実行する場合は、`.env`ファイルにDB接続情報を設定してください。

```env
# .env
ORACLE_DSN=your_database_dsn
ORACLE_USER=your_user
ORACLE_PASSWORD=your_password
```

---

## テストの実行方法

### 全テストの実行

```bash
# すべてのテストを実行
pytest

# より詳細な出力
pytest -v

# カバレッジレポートを含めて実行
pytest --cov=app --cov-report=html
```

### 特定のテストカテゴリーのみ実行

```bash
# 単体テストのみ
pytest -m unit

# 統合テストのみ
pytest -m integration

# E2Eテストのみ
pytest -m e2e

# 認証関連のテストのみ
pytest -m auth

# 申請機能のテストのみ
pytest -m application

# ワークフローテストのみ
pytest -m workflow
```

### 特定のテストファイルまたはテストケースの実行

```bash
# 特定のテストファイル
pytest tests/unit/test_auth.py

# 特定のテストクラス
pytest tests/unit/test_auth.py::TestLogin

# 特定のテストケース
pytest tests/unit/test_auth.py::TestLogin::test_login_with_valid_user_dev_mode
```

### 実行時間が長いテストを除外

```bash
# slowマーカーのテストを除外
pytest -m "not slow"
```

### データベースアクセスを伴うテストのみ実行

⚠️ **警告**: 実DBを使用するテストは既存データを更新する可能性があります。
テスト専用DBを準備してから実行してください。詳細は [DATABASE_TESTING.md](DATABASE_TESTING.md) 参照。

```bash
# dbマーカーのテスト（Mock DB使用）
set USE_MOCK_DB=True  # Windows
pytest -m db

# テスト専用DBを使用する場合（上級者向け）
# .env.test を用意してから実行
pytest -m db
```

---

## テスト構成

```
tests/
├── conftest.py              # 共通フィクスチャ定義
├── __init__.py
├── unit/                    # 単体テスト
│   ├── __init__.py
│   ├── test_auth.py         # 認証・認可テスト
│   ├── test_application.py  # 申請機能テスト
│   ├── test_workflow.py     # ワークフロー・承認テスト
│   └── test_validation.py   # バリデーション・プルダウンテスト
├── integration/             # 統合テスト
│   ├── __init__.py
│   └── test_application_flow.py  # 申請フロー統合テスト
├── e2e/                     # エンドツーエンドテスト
│   ├── __init__.py
│   └── test_complete_workflow.py  # 完全なワークフローテスト
└── fixtures/                # テストデータ
    ├── __init__.py
    └── test_data.py         # テストデータ定義
```

---

## テストカテゴリー

### 単体テスト (Unit Tests)

- **マーカー**: `@pytest.mark.unit`
- **対象**: Models, Services, Utils層の個別機能
- **実行時間**: 高速（数秒）
- **データベース**: Mock DB使用

#### 含まれるテスト

1. **認証・認可テスト** (`test_auth.py`)
   - ログイン/ログアウト
   - 所属選択
   - Entra ID Easy Auth（staging/production環境）
   - 管理者権限チェック

2. **申請機能テスト** (`test_application.py`)
   - 申請一覧表示
   - 新規申請作成
   - 申請修正
   - 申請削除
   - 複数レコード形式の申請

3. **ワークフロー・承認テスト** (`test_workflow.py`)
   - 承認タスク一覧
   - 承認タスク詳細
   - 承認/却下/差し戻しアクション
   - ワークフロー進捗管理
   - 承認者選択
   - スキップロジック

4. **バリデーション・プルダウンテスト** (`test_validation.py`)
   - 必須フィールドバリデーション
   - フォーマットバリデーション
   - 正規表現バリデーション
   - クロスフィールドバリデーション
   - 静的プルダウン
   - 動的プルダウン

### 統合テスト (Integration Tests)

- **マーカー**: `@pytest.mark.integration`
- **対象**: 複数コンポーネント間の連携
- **実行時間**: 中程度（数十秒）
- **データベース**: Mock DBまたは実DB

#### 含まれるテスト

1. **申請作成フロー**
   - 申請種類選択 → 申請作成 → 提出
2. **承認フロー**
   - 承認タスク一覧 → 承認実行 → 次ノードへ進行
3. **複数ノードワークフロー**
   - 複数段階の承認処理
4. **申請修正フロー**
   - 既存リソースの修正申請
5. **所属承認ロジック**
   - 所管承認のスキップ判定

### エンドツーエンドテスト (E2E Tests)

- **マーカー**: `@pytest.mark.e2e`
- **対象**: ユーザー視点での完全なフロー
- **実行時間**: 長い（数分）
- **データベース**: Mock DBまたは実DB

#### 含まれるテスト

1. **完全な申請ワークフロー**
   - ログイン → 申請作成 → 承認 → 完了
2. **複数承認者によるワークフロー**
   - 順次承認処理
3. **エラーハンドリング**
   - 不正な入力に対するエラー処理
4. **回帰シナリオ**
   - 主要な業務シナリオの動作確認

---

## テストデータ

テストデータは `tests/fixtures/test_data.py` に定義されています。

### 主要なテストデータ

- **ユーザー**: 申請者、承認者1、承認者2、管理者
- **申請種類**: Gmailグループ作成、ユーザー権限変更、データベース権限申請
- **ワークフロー定義**: 標準承認フロー、複雑な承認フロー、部長承認フロー
- **プルダウンデータ**: ユーザー一覧、権限レベルなど

### テストデータの使用方法

```python
from tests.fixtures import get_user, get_application_type

def test_example():
    user = get_user('applicant')
    assert user['user_id'] == 'test_applicant'
    
    app_type = get_application_type(1)
    assert app_type['application_type_name'] == 'Gmailグループ作成'
```

---

## カバレッジレポート

### HTMLレポートの生成

```bash
pytest --cov=app --cov-report=html:htmlcov
```

レポートは `htmlcov/index.html` に生成されます。ブラウザで開いて確認してください。

### ターミナルでのカバレッジ表示

```bash
pytest --cov=app --cov-report=term-missing
```

### カバレッジ目標

- **全体**: 80%以上
- **重要なビジネスロジック**: 90%以上
- **Routes層**: 70%以上
- **Models層**: 85%以上
- **Services層**: 90%以上

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. `ModuleNotFoundError: No module named 'app'`

**原因**: Pythonパスが正しく設定されていない

**解決方法**:
```bash
# プロジェクトルートディレクトリで実行
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%cd%  # Windows
```

または、`conftest.py`で自動的にパスが追加されるため、プロジェクトルートで実行してください。

#### 2. データベース接続エラー

**原因**: 実DBを使用するテストで接続情報が不正

**解決方法**:
- Mock DBモードを使用: 環境変数 `USE_MOCK_DB=True` を設定（推奨）
- または `.env` ファイルのDB接続情報を確認

⚠️ **重要**: 実DBを使ったテストは既存データを更新する可能性があります。
詳細は [DATABASE_TESTING.md](DATABASE_TESTING.md) を参照してください。

#### 3. テストが遅い

**原因**: 実DBアクセスやE2Eテストを含めて実行している

**解決方法**:
```bash
# 単体テストのみ実行
pytest -m unit

# slowテストを除外
pytest -m "not slow"
```

#### 4. フィクスチャが見つからない

**原因**: `conftest.py` が正しく読み込まれていない

**解決方法**:
- `tests/` ディレクトリに `__init__.py` が存在することを確認
- `pytest` をプロジェクトルートから実行

---

## CI/CDでのテスト実行

### GitHub Actions の例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest -m "unit or integration" --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## テストの追加方法

### 新しいテストケースの追加

1. 適切なディレクトリにテストファイルを作成（`test_*.py`）
2. テストクラスを定義（`Test*`で始まる）
3. テストメソッドを追加（`test_*`で始まる）
4. 適切なマーカーを付与（`@pytest.mark.unit`など）

```python
import pytest

@pytest.mark.unit
@pytest.mark.application
class TestNewFeature:
    """新機能のテスト"""
    
    def test_new_feature_basic(self, auth_client):
        """新機能の基本動作"""
        response = auth_client.get('/new-feature')
        assert response.status_code == 200
```

---

## まとめ

- **日常的な開発**: `pytest -m unit` で単体テストを高速実行
- **PR前の確認**: `pytest -m "unit or integration"` で統合テストまで実行
- **リリース前の確認**: `pytest` で全テスト実行（E2E含む）
- **カバレッジ確認**: `pytest --cov=app --cov-report=html`

テストは継続的に追加・更新し、システムの品質を維持してください。
