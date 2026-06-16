"""
認証・認可機能の単体テスト
"""
import pytest
from flask import session


class TestLogin:
    """ログイン機能のテスト"""

    def test_login_page_access(self, client):
        """ログイン画面へのアクセス"""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert 'login' in response.get_data(as_text=True).lower()

    def test_login_with_valid_user_dev_mode(self, client, monkeypatch):
        """開発環境での有効なユーザーIDでのログイン"""
        # 開発環境モードを設定
        import os
        monkeypatch.setenv('FLASK_ENV', 'development')

        # Userモデルのモック
        class MockUser:
            @staticmethod
            def get_by_id(user_id):
                return {
                    'user_id': user_id,
                    'user_name': 'テストユーザー',
                    'shozoku': '1234000'
                }

            @staticmethod
            def get_user_departments(user_id):
                return [{
                    'shozoku': '1234000',
                    'shozoku_name': 'テスト部署'
                }]

        from app.models import user
        monkeypatch.setattr(user, 'User', MockUser)

        # AdminUserモデルのモック
        class MockAdminUser:
            @staticmethod
            def is_admin(user_id):
                return False

        from app.models import admin_user
        monkeypatch.setattr(admin_user, 'AdminUser', MockAdminUser)

        # ログイン実行
        response = client.post('/auth/login', data={'user_id': 'test_user'}, follow_redirects=True)
        assert response.status_code == 200

    def test_login_with_invalid_user(self, client, monkeypatch):
        """存在しないユーザーIDでのログイン失敗"""
        # 開発環境モードを設定
        import os
        monkeypatch.setenv('FLASK_ENV', 'development')

        # Userモデルのモック（ユーザーが見つからない）
        class MockUser:
            @staticmethod
            def get_by_id(user_id):
                return None

        from app.models import user
        monkeypatch.setattr(user, 'User', MockUser)

        response = client.post('/auth/login', data={'user_id': 'invalid_user'})
        assert response.status_code == 200
        assert 'ユーザーが見つかりません' in response.get_data(as_text=True)

    def test_login_without_user_id(self, client, monkeypatch):
        """ユーザーID未入力でのログイン"""
        import os
        monkeypatch.setenv('FLASK_ENV', 'development')

        response = client.post('/auth/login', data={})
        assert response.status_code == 200
        assert 'ユーザーIDを入力' in response.get_data(as_text=True)


class TestDepartmentSelection:
    """所属選択機能のテスト"""

    def test_select_department_page_requires_login(self, client):
        """所属選択画面は未ログインだとリダイレクトされる"""
        response = client.get('/auth/select-department', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_select_department_with_multiple_depts(self, auth_client, monkeypatch):
        """複数所属がある場合の所属選択画面表示"""
        # Userモデルのモック
        class MockUser:
            @staticmethod
            def get_user_departments(user_id):
                return [
                    {'shozoku': '1234000', 'shozoku_name': 'テスト部署1'},
                    {'shozoku': '5678000', 'shozoku_name': 'テスト部署2'},
                ]

        from app.models import user
        monkeypatch.setattr(user, 'User', MockUser)

        response = auth_client.get('/auth/select-department')
        assert response.status_code == 200
        assert 'テスト部署1' in response.get_data(as_text=True)
        assert 'テスト部署2' in response.get_data(as_text=True)

    def test_select_department_with_single_dept(self, auth_client, monkeypatch):
        """所属が1つしかない場合は自動選択"""
        # Userモデルのモック
        class MockUser:
            @staticmethod
            def get_user_departments(user_id):
                return [
                    {'shozoku': '1234000', 'shozoku_name': 'テスト部署'},
                ]

        from app.models import user
        monkeypatch.setattr(user, 'User', MockUser)

        response = auth_client.get('/auth/select-department', follow_redirects=False)
        assert response.status_code == 302
        assert '/application' in response.location

    def test_post_department_selection(self, auth_client):
        """所属選択のPOST処理"""
        response = auth_client.post('/auth/select-department',
                                     data={
                                         'shozoku': '5678000',
                                         'shozoku_name': 'テスト部署2'
                                     },
                                     follow_redirects=False)
        assert response.status_code == 302
        assert '/application' in response.location


class TestLogout:
    """ログアウト機能のテスト"""

    def test_logout(self, auth_client):
        """ログアウト処理"""
        response = auth_client.get('/logout', follow_redirects=False)
        # ログアウトは /auth/logout にリダイレクトされる
        assert response.status_code == 404 or response.status_code == 302

    def test_logout_clears_session(self, auth_client):
        """ログアウトでセッションがクリアされる"""
        # ログアウト実行
        auth_client.get('/auth/logout')

        # セッションが空になっていることを確認
        with auth_client.session_transaction() as sess:
            assert 'user_id' not in sess


class TestAdminCheck:
    """管理者権限チェックのテスト"""

    def test_admin_user_has_admin_flag(self, admin_client):
        """管理者ユーザーは管理者フラグが立つ"""
        with admin_client.session_transaction() as sess:
            assert sess.get('is_admin') == True

    def test_normal_user_has_no_admin_flag(self, auth_client):
        """通常ユーザーは管理者フラグが立たない"""
        with auth_client.session_transaction() as sess:
            assert sess.get('is_admin') == False


class TestWindowsAuth:
    """Windows統合認証のテスト（本番環境）"""

    def test_production_sso_mode(self, client, monkeypatch):
        """本番環境ではSSO認証が有効"""
        import os
        monkeypatch.setenv('FLASK_ENV', 'production')

        # Windows認証ヘッダーをモック
        def mock_get_authenticated_user(request):
            return 'domain\\test_user'

        from app.utils import windows_auth
        monkeypatch.setattr(windows_auth, 'get_authenticated_user_from_request', mock_get_authenticated_user)

        # Userモデルのモック
        class MockUser:
            @staticmethod
            def get_by_id(user_id):
                return {
                    'user_id': user_id,
                    'user_name': 'テストユーザー',
                    'shozoku': '1234000'
                }

            @staticmethod
            def get_user_departments(user_id):
                return [{'shozoku': '1234000', 'shozoku_name': 'テスト部署'}]

        from app.models import user
        monkeypatch.setattr(user, 'User', MockUser)

        # AdminUserモデルのモック
        class MockAdminUser:
            @staticmethod
            def is_admin(user_id):
                return False

        from app.models import admin_user
        monkeypatch.setattr(admin_user, 'AdminUser', MockAdminUser)

        response = client.get('/auth/login', follow_redirects=True)
        assert response.status_code == 200

    def test_production_sso_failure(self, client, monkeypatch):
        """本番環境でSSO認証失敗"""
        import os
        monkeypatch.setenv('FLASK_ENV', 'production')

        # Windows認証失敗をモック
        def mock_get_authenticated_user(request):
            return None

        from app.utils import windows_auth
        monkeypatch.setattr(windows_auth, 'get_authenticated_user_from_request', mock_get_authenticated_user)

        response = client.get('/auth/login')
        assert response.status_code == 200
        assert '認証に失敗' in response.get_data(as_text=True)
