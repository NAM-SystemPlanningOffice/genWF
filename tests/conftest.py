"""
Pytestの共通フィクスチャ定義
"""
import os
import sys
import pytest
from datetime import datetime

# アプリケーションのパスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope='session')
def app():
    """Flaskアプリケーションのフィクスチャ（セッションスコープ）"""
    # テストモードでMock DBを使用
    os.environ['USE_MOCK_DB'] = 'True'
    os.environ['FLASK_ENV'] = 'testing'

    from app import create_app
    app = create_app('testing')

    yield app


@pytest.fixture(scope='function')
def client(app):
    """テストクライアントのフィクスチャ（関数スコープ）"""
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='function')
def runner(app):
    """CLIランナーのフィクスチャ"""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def auth_client(client):
    """認証済みテストクライアント"""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_user'
        sess['user_name'] = 'テストユーザー'
        sess['shozoku'] = '1234000'
        sess['shozoku_name'] = 'テスト部署'
        sess['is_admin'] = False
    yield client


@pytest.fixture(scope='function')
def admin_client(client):
    """管理者権限の認証済みテストクライアント"""
    with client.session_transaction() as sess:
        sess['user_id'] = 'admin_user'
        sess['user_name'] = '管理者ユーザー'
        sess['shozoku'] = '1234000'
        sess['shozoku_name'] = 'システム企画室'
        sess['is_admin'] = True
    yield client


@pytest.fixture(scope='function')
def sample_application_data():
    """サンプル申請データ"""
    return {
        'application_type_id': 1,
        'action_type': 'create',
        'applicant_user_id': 'test_user',
        'applicant_shozoku': '1234000',
        'jurisdiction_shozoku': '1234000',
        'application_title': 'テスト申請',
        'remarks': '回帰テスト用データ'
    }


@pytest.fixture(scope='function')
def sample_field_data():
    """サンプルフィールドデータ"""
    return [
        {
            'field_id': 1,
            'field_name': 'resource_name',
            'field_type': 'text',
            'field_value': 'テストリソース',
            'is_required': True
        },
        {
            'field_id': 2,
            'field_name': 'start_date',
            'field_type': 'date',
            'field_value': '2026-06-15',
            'is_required': True
        }
    ]


@pytest.fixture(scope='function')
def sample_workflow_data():
    """サンプルワークフローデータ"""
    return {
        'workflow_definition_id': 1,
        'application_id': 1,
        'workflow_status': 'in_progress',
        'current_node_seq': 1
    }


@pytest.fixture(scope='function')
def mock_db_connection(monkeypatch):
    """モックDB接続"""
    class MockCursor:
        def __init__(self):
            self.description = None
            self.rowcount = 0

        def execute(self, sql, params=None):
            pass

        def fetchone(self):
            return None

        def fetchall(self):
            return []

        def close(self):
            pass

    class MockConnection:
        def cursor(self):
            return MockCursor()

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    def mock_get_connection():
        return MockConnection()

    from app.utils import db
    monkeypatch.setattr(db, 'get_db_connection', mock_get_connection)


@pytest.fixture(autouse=True)
def reset_test_state():
    """各テスト実行前後の状態リセット"""
    # テスト前の処理
    yield
    # テスト後の処理（必要に応じて）


@pytest.fixture(scope='function')
def freeze_time(monkeypatch):
    """時刻を固定するフィクスチャ"""
    frozen_time = datetime(2026, 6, 15, 10, 0, 0)

    class MockDatetime:
        @classmethod
        def now(cls):
            return frozen_time

    import datetime as dt_module
    monkeypatch.setattr(dt_module, 'datetime', MockDatetime)

    return frozen_time


@pytest.fixture(scope='function')
def save_html(request):
    """HTMLレスポンスを保存するヘルパー"""
    import os
    from datetime import datetime

    output_dir = 'test_results/html'
    os.makedirs(output_dir, exist_ok=True)

    def _save(response, filename=None):
        if filename is None:
            # テスト名から自動生成
            test_name = request.node.name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{test_name}_{timestamp}.html'

        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.get_data(as_text=True))

        print(f'\n✅ HTML保存: {filepath}')
        return filepath

    return _save


@pytest.fixture(scope='function')
def save_screenshot():
    """スクリーンショットを保存するヘルパー"""
    import os

    output_dir = 'test_results/screenshots'
    os.makedirs(output_dir, exist_ok=True)

    def _save(driver, filename):
        from datetime import datetime

        if not filename.endswith('.png'):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{filename}_{timestamp}.png'

        filepath = os.path.join(output_dir, filename)
        driver.save_screenshot(filepath)
        print(f'\n✅ スクリーンショット保存: {filepath}')
        return filepath

    return _save
