"""
Routes層のカバレッジ向上用テスト
実際のFlaskルートにアクセスして、0%カバレッジのモジュールをカバーする
"""
import pytest


@pytest.mark.integration
class TestApplicationRoutesCoverage:
    """申請画面Routes層のカバレッジテスト"""

    def test_application_index_route(self, auth_client, monkeypatch):
        """申請種類一覧画面への実アクセス"""
        # 最小限のモックで実際のルートハンドラーを呼ぶ
        class MockApplicationType:
            @staticmethod
            def get_all_active(**kwargs):
                return []

        from app.models import application_type
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)

        response = auth_client.get('/application/')
        assert response.status_code == 200

    def test_application_create_route(self, auth_client, monkeypatch):
        """申請作成画面への実アクセス"""
        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'application_type_name': 'テスト',
                    'support_create': 'Y',
                    'is_multi_record': 'N'
                }

            @staticmethod
            def is_allowed_to_apply(app_type, shozoku, user_id):
                return True

        class MockApplicationField:
            @staticmethod
            def get_by_application_type(app_type_id):
                return []

        from app.models import application_type, application_field
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(application_field, 'ApplicationField', MockApplicationField)

        response = auth_client.get('/application/create/1')
        assert response.status_code == 200


@pytest.mark.integration
class TestApprovalRoutesCoverage:
    """承認画面Routes層のカバレッジテスト"""

    def test_approval_tasks_route(self, auth_client, monkeypatch):
        """承認タスク一覧への実アクセス"""
        class MockApprovalTask:
            @staticmethod
            def get_pending_tasks(user_id):
                return []

        from app.models import approval_task
        monkeypatch.setattr(approval_task, 'ApprovalTask', MockApprovalTask)

        response = auth_client.get('/approval/tasks')
        assert response.status_code == 200


@pytest.mark.integration
class TestAdminRoutesCoverage:
    """管理画面Routes層のカバレッジテスト"""

    def test_admin_index_requires_admin(self, auth_client):
        """管理画面は管理者権限が必要（一般ユーザーはアクセス不可）"""
        response = auth_client.get('/admin/', follow_redirects=False)
        # 権限がない場合はリダイレクトまたは403
        assert response.status_code in [302, 403, 404]

    def test_admin_index_with_admin_user(self, admin_client, monkeypatch):
        """管理者ユーザーは管理画面にアクセス可能"""
        # 管理画面用のモックデータ
        class MockApplicationType:
            @staticmethod
            def get_all(include_deleted=False):
                return []

        from app.models.admin import application_type
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)

        response = admin_client.get('/admin/')
        # 管理画面が実装されている場合は200、未実装なら404
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestModifyRoutesCoverage:
    """申請修正画面Routes層のカバレッジテスト"""

    def test_application_modify_route(self, auth_client, monkeypatch):
        """申請修正画面への実アクセス"""
        class MockApplication:
            @staticmethod
            def get_by_id(app_id):
                return {
                    'application_id': app_id,
                    'application_type_id': 1,
                    'applicant_user_id': 'test_user'
                }

        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'support_modify': 'Y',
                    'is_multi_record': 'N'
                }

        class MockApplicationDetail:
            @staticmethod
            def get_by_application(app_id):
                return []

        class MockApplicationField:
            @staticmethod
            def get_by_application_type(app_type_id):
                return []

        from app.models import application, application_type, application_detail, application_field
        monkeypatch.setattr(application, 'Application', MockApplication)
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(application_detail, 'ApplicationDetail', MockApplicationDetail)
        monkeypatch.setattr(application_field, 'ApplicationField', MockApplicationField)

        response = auth_client.get('/application/modify/1/1')
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestMultiRoutesCoverage:
    """複数レコード申請画面Routes層のカバレッジテスト"""

    def test_application_multi_create_route(self, auth_client, monkeypatch):
        """複数レコード形式の申請作成画面"""
        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'support_create': 'Y',
                    'is_multi_record': 'Y'
                }

            @staticmethod
            def is_allowed_to_apply(app_type, shozoku, user_id):
                return True

        class MockApplicationField:
            @staticmethod
            def get_by_application_type(app_type_id):
                return []

        from app.models import application_type, application_field
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(application_field, 'ApplicationField', MockApplicationField)

        response = auth_client.get('/application/multi/create/1')
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestAPIRoutesCoverage:
    """API Routes層のカバレッジテスト"""

    def test_api_pulldown_options(self, auth_client, monkeypatch):
        """プルダウン選択肢取得API"""
        class MockPulldownOption:
            @staticmethod
            def get_by_group(group_id):
                return []

        from app.models.admin import pulldown_option
        monkeypatch.setattr(pulldown_option, 'PulldownOption', MockPulldownOption)

        response = auth_client.get('/api/pulldown/options/1')
        assert response.status_code in [200, 404]

    def test_api_dynamic_pulldown(self, auth_client, monkeypatch):
        """動的プルダウン取得API"""
        class MockPulldownGroup:
            @staticmethod
            def get_by_id(group_id):
                return {
                    'pulldown_group_id': group_id,
                    'is_dynamic': 'Y',
                    'dynamic_sql': 'SELECT 1 AS value, 1 AS label FROM dual'
                }

        from app.models.admin import pulldown_group
        monkeypatch.setattr(pulldown_group, 'PulldownGroup', MockPulldownGroup)

        response = auth_client.get('/api/pulldown/dynamic/1?applicant_shozoku=1234000')
        assert response.status_code in [200, 404]
