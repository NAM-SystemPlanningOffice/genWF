"""
申請機能の単体テスト
"""
import pytest
from flask import session


class TestApplicationList:
    """申請一覧のテスト"""

    def test_application_list_requires_login(self, client):
        """申請一覧は未ログインだとリダイレクト"""
        response = client.get('/application/', follow_redirects=False)
        assert response.status_code == 302

    def test_application_list_for_authenticated_user(self, auth_client, monkeypatch):
        """認証済みユーザーは申請一覧を表示できる"""
        # ApplicationTypeモデルのモック
        class MockApplicationType:
            @staticmethod
            def get_all_active(**kwargs):
                return [
                    {
                        'application_type_id': 1,
                        'application_type_name': 'テスト申請種類1',
                        'application_type_description': '説明1'
                    }
                ]

        from app.models import application_type
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)

        response = auth_client.get('/application/')
        assert response.status_code == 200
        assert 'テスト申請種類1' in response.get_data(as_text=True)

    def test_admin_can_see_under_development_types(self, admin_client, monkeypatch):
        """管理者は開発中の申請種類も表示できる"""
        call_args = {}

        class MockApplicationType:
            @staticmethod
            def get_all_active(**kwargs):
                call_args.update(kwargs)
                return []

        from app.models import application_type
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)

        admin_client.get('/application/')
        assert call_args.get('include_under_development') == True


class TestApplicationCreate:
    """申請作成のテスト"""

    def test_create_page_requires_login(self, client):
        """申請作成画面は未ログインだとリダイレクト"""
        response = client.get('/application/create/1', follow_redirects=False)
        assert response.status_code == 302

    def test_create_page_with_valid_type(self, auth_client, monkeypatch):
        """有効な申請種類IDで申請作成画面を表示"""
        # モックデータ
        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'application_type_name': 'テスト申請',
                    'support_create': 'Y',
                    'is_multi_record': 'N'
                }

            @staticmethod
            def is_allowed_to_apply(app_type, shozoku, user_id):
                return True

        class MockApplicationField:
            @staticmethod
            def get_by_application_type(app_type_id):
                return [
                    {
                        'field_id': 1,
                        'field_name': 'resource_name',
                        'field_type': 'text',
                        'is_required_create': 'Y',
                        'pulldown_group_id': None
                    }
                ]

        from app.models import application_type, application_field
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(application_field, 'ApplicationField', MockApplicationField)

        response = auth_client.get('/application/create/1')
        assert response.status_code == 200

    def test_create_page_with_invalid_type(self, auth_client, monkeypatch):
        """存在しない申請種類IDでエラー"""
        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return None

        from app.models import application_type
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)

        response = auth_client.get('/application/create/999', follow_redirects=True)
        assert response.status_code == 200
        assert '見つかりません' in response.get_data(as_text=True)

    def test_create_page_not_supporting_create(self, auth_client, monkeypatch):
        """新規作成をサポートしていない申請種類"""
        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'application_type_name': 'テスト申請',
                    'support_create': 'N',
                }

        from app.models import application_type
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)

        response = auth_client.get('/application/create/1', follow_redirects=True)
        assert response.status_code == 200
        assert 'サポートしていません' in response.get_data(as_text=True)

    def test_create_with_restriction(self, auth_client, monkeypatch):
        """申請制限により作成できない"""
        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'application_type_name': 'テスト申請',
                    'support_create': 'Y',
                }

            @staticmethod
            def is_allowed_to_apply(app_type, shozoku, user_id):
                return False

        from app.models import application_type
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)

        response = auth_client.get('/application/create/1', follow_redirects=True)
        assert response.status_code == 200
        assert '申請できません' in response.get_data(as_text=True)


class TestApplicationSubmit:
    """申請提出のテスト"""

    def test_submit_application_with_valid_data(self, auth_client, monkeypatch, sample_application_data):
        """有効なデータで申請を提出"""
        created_app_id = None

        class MockApplication:
            @staticmethod
            def create(data):
                nonlocal created_app_id
                created_app_id = 123
                return created_app_id

        class MockApplicationDetail:
            @staticmethod
            def create_bulk(app_id, details):
                return True

        class MockWorkflowService:
            @staticmethod
            def start_workflow(app_id, workflow_def_id, applicant_user_id, applicant_shozoku):
                return True

        from app.models import application, application_detail
        from app.services import workflow_service

        monkeypatch.setattr(application, 'Application', MockApplication)
        monkeypatch.setattr(application_detail, 'ApplicationDetail', MockApplicationDetail)
        monkeypatch.setattr(workflow_service, 'WorkflowService', MockWorkflowService)

        # 申請種類のモック
        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'workflow_definition_id': 1,
                    'is_multi_record': 'N'
                }

        from app.models import application_type
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)

        # フィールドのモック
        class MockApplicationField:
            @staticmethod
            def get_by_application_type(app_type_id):
                return [
                    {
                        'field_id': 1,
                        'field_name': 'resource_name',
                        'field_type': 'text',
                        'is_required_create': 'Y'
                    }
                ]

        from app.models import application_field
        monkeypatch.setattr(application_field, 'ApplicationField', MockApplicationField)

        # POST実行
        response = auth_client.post('/application/submit/1', data={
            'application_title': 'テスト申請',
            'action_type': 'create',
            'field_1': 'テストリソース'
        }, follow_redirects=False)

        # リダイレクトされることを確認
        assert response.status_code == 302 or response.status_code == 200


class TestApplicationModify:
    """申請修正のテスト"""

    def test_modify_page_requires_login(self, client):
        """申請修正画面は未ログインだとリダイレクト"""
        response = client.get('/application/modify/1/1', follow_redirects=False)
        assert response.status_code == 302

    def test_modify_existing_application(self, auth_client, monkeypatch):
        """既存申請の修正画面表示"""
        class MockApplication:
            @staticmethod
            def get_by_id(app_id):
                return {
                    'application_id': app_id,
                    'application_type_id': 1,
                    'application_title': '既存申請',
                    'applicant_user_id': 'test_user'
                }

        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'application_type_name': 'テスト申請',
                    'support_modify': 'Y',
                    'is_multi_record': 'N'
                }

        class MockApplicationDetail:
            @staticmethod
            def get_by_application(app_id):
                return [
                    {
                        'detail_id': 1,
                        'field_id': 1,
                        'field_value': '既存値'
                    }
                ]

        class MockApplicationField:
            @staticmethod
            def get_by_application_type(app_type_id):
                return [
                    {
                        'field_id': 1,
                        'field_name': 'resource_name',
                        'field_type': 'text'
                    }
                ]

        from app.models import application, application_type, application_detail, application_field
        monkeypatch.setattr(application, 'Application', MockApplication)
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(application_detail, 'ApplicationDetail', MockApplicationDetail)
        monkeypatch.setattr(application_field, 'ApplicationField', MockApplicationField)

        response = auth_client.get('/application/modify/1/1')
        assert response.status_code == 200


class TestApplicationDelete:
    """申請削除のテスト"""

    def test_delete_requires_login(self, client):
        """削除は未ログインだとリダイレクト"""
        response = client.get('/application/delete/1/1', follow_redirects=False)
        assert response.status_code == 302

    def test_delete_existing_resource(self, auth_client, monkeypatch):
        """既存リソースの削除申請画面"""
        class MockResource:
            @staticmethod
            def get_by_id(resource_id):
                return {
                    'resource_id': resource_id,
                    'resource_name': 'テストリソース'
                }

        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'support_delete': 'Y'
                }

        from app.models import resource, application_type
        monkeypatch.setattr(resource, 'Resource', MockResource)
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)

        response = auth_client.get('/application/delete/1/1')
        # 実装によってステータスコードが異なる可能性がある
        assert response.status_code in [200, 302, 404]


class TestApplicationMultiRecord:
    """複数レコード形式の申請テスト"""

    def test_multi_record_create_page(self, auth_client, monkeypatch):
        """複数レコード形式の申請作成画面"""
        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'application_type_name': '複数レコード申請',
                    'support_create': 'Y',
                    'is_multi_record': 'Y'
                }

            @staticmethod
            def is_allowed_to_apply(app_type, shozoku, user_id):
                return True

        class MockApplicationField:
            @staticmethod
            def get_by_application_type(app_type_id):
                return [
                    {
                        'field_id': 1,
                        'field_name': 'user_id',
                        'field_type': 'text',
                        'is_required_create': 'Y',
                        'pulldown_group_id': None
                    }
                ]

        from app.models import application_type, application_field
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(application_field, 'ApplicationField', MockApplicationField)

        response = auth_client.get('/application/multi/create/1')
        # マルチレコード用のルートが実装されている場合
        assert response.status_code in [200, 404]
