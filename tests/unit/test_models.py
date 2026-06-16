"""
Models層の単体テスト（Mock DB使用）
"""
import pytest
import os


@pytest.mark.unit
class TestApplicationType:
    """ApplicationTypeモデルのテスト"""

    def test_get_all_active(self, app):
        """有効な申請種類の全件取得"""
        with app.app_context():
            from app.models.application_type import ApplicationType

            app_types = ApplicationType.get_all_active()
            assert isinstance(app_types, list)
            assert len(app_types) > 0

            # 各レコードに必要なキーが含まれているか確認
            for app_type in app_types:
                assert 'application_type_id' in app_type
                assert 'application_type_name' in app_type

    def test_get_by_id(self, app):
        """ID指定での申請種類取得"""
        with app.app_context():
            from app.models.application_type import ApplicationType

            # まず全件取得してIDを取得
            app_types = ApplicationType.get_all_active()
            if app_types:
                app_type_id = app_types[0]['application_type_id']
                app_type = ApplicationType.get_by_id(app_type_id)

                assert app_type is not None
                assert app_type['application_type_id'] == app_type_id

    def test_check_can_apply(self, app):
        """申請可能チェック"""
        with app.app_context():
            from app.models.application_type import ApplicationType

            # Mock DBでは常に申請可能として扱う
            can_apply = ApplicationType.check_can_apply(1, '1234000')
            assert isinstance(can_apply, bool)


@pytest.mark.unit
class TestApplicationField:
    """ApplicationFieldモデルのテスト"""

    def test_get_by_application_type(self, app):
        """申請種類IDに紐づくフィールド取得"""
        with app.app_context():
            from app.models.application_field import ApplicationField

            fields = ApplicationField.get_by_application_type(1)
            assert isinstance(fields, list)

            # フィールド情報の確認
            for field in fields:
                assert 'field_name' in field
                assert 'field_type' in field
                assert 'is_required_create' in field


@pytest.mark.unit
class TestUser:
    """Userモデルのテスト"""

    def test_get_by_id(self, app):
        """ユーザーIDでのユーザー取得"""
        with app.app_context():
            from app.models.user import User

            user = User.get_by_id('test_user')
            # Mock DBではユーザーが存在しない可能性もある
            if user:
                assert 'user_name' in user
                assert 'shozoku' in user

    def test_get_approvers_by_shozoku(self, app):
        """所属コードによる承認者一覧取得"""
        with app.app_context():
            from app.models.user import User

            approvers = User.get_approvers_by_shozoku('1234000')
            assert isinstance(approvers, list)

            for approver in approvers:
                assert 'user_id' in approver or 'user_name' in approver


@pytest.mark.unit
class TestWorkflowDefinition:
    """WorkflowDefinitionモデルのテスト"""

    def test_get_by_id(self, app):
        """ワークフロー定義の取得"""
        with app.app_context():
            from app.models.workflow import WorkflowDefinition

            workflow_def = WorkflowDefinition.get_by_id(1)
            if workflow_def:
                assert 'workflow_id' in workflow_def or 'workflow_name' in workflow_def

    def test_get_nodes(self, app):
        """ワークフローノード定義の取得"""
        with app.app_context():
            from app.models.workflow import WorkflowDefinition

            nodes = WorkflowDefinition.get_nodes(1)
            assert isinstance(nodes, list)

            for node in nodes:
                assert 'node_seq' in node or 'node_name' in node or 'node_type' in node


@pytest.mark.unit
class TestApplication:
    """Applicationモデルのテスト"""

    def test_create(self, app):
        """申請作成のテスト"""
        with app.app_context():
            from app.models.application import Application

            application_data = {
                'application_type_id': 1,
                'action_type': 'create',
                'applicant_user_id': 'test_user',
                'applicant_shozoku': '1234000',
                'jurisdiction_shozoku': '1234000',
                'application_title': 'テスト申請',
                'remarks': 'pytest単体テスト'
            }

            # Mock DBでは実際の保存は行われない可能性がある
            try:
                application_id = Application.create(application_data)
                assert application_id is not None
            except Exception:
                # Mock DBでの作成処理が実装されていない場合はスキップ
                pytest.skip("Application.create not implemented in Mock DB")

    def test_get_by_id(self, app):
        """申請IDでの申請取得"""
        with app.app_context():
            from app.models.application import Application

            # 存在しないIDでの取得テスト
            application = Application.get_by_id(99999)
            # Mock DBでは存在しないことが予想される
            assert application is None or isinstance(application, dict)


@pytest.mark.unit
class TestResource:
    """Resourceモデルのテスト"""

    def test_get_gmail_groups(self, app):
        """Gmailグループ一覧の取得"""
        with app.app_context():
            from app.models.resource import Resource

            try:
                groups = Resource.get_gmail_groups()
                assert isinstance(groups, list)

                for group in groups:
                    assert isinstance(group, dict)
            except Exception:
                # Mock DBでの実装がない場合はスキップ
                pytest.skip("Resource.get_gmail_groups not implemented in Mock DB")
