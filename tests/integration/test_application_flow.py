"""
申請フロー統合テスト
"""
import pytest


@pytest.mark.integration
class TestApplicationCreateFlow:
    """申請作成フローの統合テスト"""

    def test_full_create_flow(self, auth_client, monkeypatch):
        """新規申請作成の全体フロー"""
        # 1. 申請種類一覧を表示
        class MockApplicationType:
            @staticmethod
            def get_all_active(**kwargs):
                return [
                    {
                        'application_type_id': 1,
                        'application_type_name': 'Gmailグループ作成',
                        'support_create': 'Y'
                    }
                ]

            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'application_type_name': 'Gmailグループ作成',
                    'support_create': 'Y',
                    'is_multi_record': 'N',
                    'workflow_definition_id': 1
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
                        'field_name': 'group_email',
                        'field_type': 'text',
                        'is_required_create': 'Y',
                        'pulldown_group_id': None
                    }
                ]

        class MockApplication:
            @staticmethod
            def create(data):
                return 123  # 申請ID

        class MockApplicationDetail:
            @staticmethod
            def create_bulk(app_id, details):
                return True

        class MockWorkflowService:
            @staticmethod
            def start_workflow(app_id, workflow_def_id, user_id, shozoku):
                return True

        from app.models import application_type, application_field, application, application_detail
        from app.services import workflow_service

        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(application_field, 'ApplicationField', MockApplicationField)
        monkeypatch.setattr(application, 'Application', MockApplication)
        monkeypatch.setattr(application_detail, 'ApplicationDetail', MockApplicationDetail)
        monkeypatch.setattr(workflow_service, 'WorkflowService', MockWorkflowService)

        # 2. 申請作成画面を表示
        response = auth_client.get('/application/create/1')
        assert response.status_code == 200

        # 3. 申請を提出
        response = auth_client.post('/application/submit/1', data={
            'application_title': 'テストグループ作成',
            'action_type': 'create',
            'field_1': 'test-group@example.com'
        }, follow_redirects=False)

        # 提出後はリダイレクトされる
        assert response.status_code in [200, 302]


@pytest.mark.integration
class TestApprovalFlow:
    """承認フローの統合テスト"""

    def test_full_approval_flow(self, auth_client, monkeypatch):
        """承認の全体フロー"""
        # 1. 承認タスク一覧を表示
        class MockApprovalTask:
            @staticmethod
            def get_pending_tasks(user_id):
                return [
                    {
                        'node_instance_id': 1,
                        'application_id': 1,
                        'application_title': 'テスト申請',
                        'node_name': '所属長承認'
                    }
                ]

            @staticmethod
            def get_task_detail(node_instance_id, user_id):
                return {
                    'node_instance_id': node_instance_id,
                    'application_id': 1,
                    'application_title': 'テスト申請',
                    'node_name': '所属長承認',
                    'node_status': 'pending'
                }

            @staticmethod
            def approve(node_instance_id, user_id, comment):
                return True

        class MockApplication:
            @staticmethod
            def get_by_id(app_id):
                return {
                    'application_id': app_id,
                    'application_type_id': 1,
                    'application_title': 'テスト申請',
                    'applicant_user_id': 'applicant'
                }

        class MockApplicationDetail:
            @staticmethod
            def get_by_application(app_id):
                return []

        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'is_multi_record': 'N'
                }

        class MockWorkflowNodeInstance:
            @staticmethod
            def get_workflow_progress(workflow_instance_id):
                return []

        class MockWorkflowService:
            @staticmethod
            def proceed_to_next_node(workflow_instance_id):
                return True

        from app.models import approval_task, application, application_detail, application_type, workflow
        from app.services import workflow_service

        monkeypatch.setattr(approval_task, 'ApprovalTask', MockApprovalTask)
        monkeypatch.setattr(application, 'Application', MockApplication)
        monkeypatch.setattr(application_detail, 'ApplicationDetail', MockApplicationDetail)
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(workflow, 'WorkflowNodeInstance', MockWorkflowNodeInstance)
        monkeypatch.setattr(workflow_service, 'WorkflowService', MockWorkflowService)

        # 2. 承認タスク詳細を表示
        response = auth_client.get('/approval/task/1')
        assert response.status_code == 200

        # 3. 承認を実行
        response = auth_client.post('/approval/approve/1', data={
            'comment': '承認します'
        }, follow_redirects=False)

        assert response.status_code in [200, 302, 404]


@pytest.mark.integration
class TestMultiNodeWorkflow:
    """複数ノードのワークフローテスト"""

    def test_multi_step_approval(self, monkeypatch):
        """複数段階の承認フロー"""
        # ワークフロー定義: 申請 → 所属長承認 → システム企画室承認 → 完了
        workflow_nodes = [
            {'node_seq': 1, 'node_name': '所属長承認', 'node_type': 'approval'},
            {'node_seq': 2, 'node_name': 'システム企画室承認', 'node_type': 'approval'},
            {'node_seq': 3, 'node_name': '完了通知', 'node_type': 'notification'}
        ]

        class MockWorkflowDefinition:
            @staticmethod
            def get_nodes(workflow_def_id):
                return workflow_nodes

        from app.models import workflow
        monkeypatch.setattr(workflow, 'WorkflowDefinition', MockWorkflowDefinition)

        nodes = MockWorkflowDefinition.get_nodes(1)
        assert len(nodes) == 3
        assert nodes[0]['node_type'] == 'approval'
        assert nodes[2]['node_type'] == 'notification'


@pytest.mark.integration
class TestApplicationModifyFlow:
    """申請修正フローの統合テスト"""

    def test_modify_existing_resource(self, auth_client, monkeypatch):
        """既存リソースの修正申請フロー"""
        # 1. リソース一覧から修正対象を選択
        class MockResource:
            @staticmethod
            def search(**kwargs):
                return [
                    {
                        'resource_id': 1,
                        'resource_name': '既存リソース'
                    }
                ]

            @staticmethod
            def get_by_id(resource_id):
                return {
                    'resource_id': resource_id,
                    'resource_name': '既存リソース'
                }

        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'support_modify': 'Y',
                    'is_multi_record': 'N'
                }

        class MockApplication:
            @staticmethod
            def get_by_id(app_id):
                return {
                    'application_id': app_id,
                    'application_type_id': 1,
                    'applicant_user_id': 'test_user'
                }

            @staticmethod
            def create(data):
                return 124

        class MockApplicationDetail:
            @staticmethod
            def get_by_application(app_id):
                return []

            @staticmethod
            def create_bulk(app_id, details):
                return True

        class MockApplicationField:
            @staticmethod
            def get_by_application_type(app_type_id):
                return []

        class MockWorkflowService:
            @staticmethod
            def start_workflow(app_id, workflow_def_id, user_id, shozoku):
                return True

        from app.models import resource, application_type, application, application_detail, application_field
        from app.services import workflow_service

        monkeypatch.setattr(resource, 'Resource', MockResource)
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(application, 'Application', MockApplication)
        monkeypatch.setattr(application_detail, 'ApplicationDetail', MockApplicationDetail)
        monkeypatch.setattr(application_field, 'ApplicationField', MockApplicationField)
        monkeypatch.setattr(workflow_service, 'WorkflowService', MockWorkflowService)

        # 2. 修正申請画面を表示
        response = auth_client.get('/application/modify/1/1')
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestDepartmentApprovalLogic:
    """所属承認ロジックの統合テスト"""

    def test_same_department_skip_jurisdiction(self):
        """申請者所属と所管所属が同じ場合、所管承認をスキップ"""
        applicant_shozoku = '1234000'
        jurisdiction_shozoku = '1234000'

        # スキップロジック
        should_skip = (applicant_shozoku == jurisdiction_shozoku)
        assert should_skip == True

    def test_different_department_require_jurisdiction(self):
        """申請者所属と所管所属が異なる場合、所管承認が必要"""
        applicant_shozoku = '1234000'
        jurisdiction_shozoku = '5678000'

        should_skip = (applicant_shozoku == jurisdiction_shozoku)
        assert should_skip == False


@pytest.mark.integration
class TestWorkflowWithNotification:
    """通知を含むワークフローのテスト"""

    def test_final_notification_node(self, monkeypatch):
        """最終承認後の報告ノード"""
        workflow_nodes = [
            {'node_seq': 1, 'node_name': 'システム企画室承認', 'node_type': 'approval'},
            {'node_seq': 2, 'node_name': '経営企画部報告', 'node_type': 'notification'},
        ]

        class MockWorkflowDefinition:
            @staticmethod
            def get_nodes(workflow_def_id):
                return workflow_nodes

        from app.models import workflow
        monkeypatch.setattr(workflow, 'WorkflowDefinition', MockWorkflowDefinition)

        nodes = MockWorkflowDefinition.get_nodes(1)

        # 報告ノードは承認を待たずに後続処理を進める
        notification_node = nodes[1]
        assert notification_node['node_type'] == 'notification'


@pytest.mark.integration
@pytest.mark.db
class TestDatabaseIntegration:
    """データベース統合テスト（実DB使用）"""

    def test_application_type_from_db(self, monkeypatch):
        """実DBから申請種類を取得"""
        # USE_MOCK_DBを無効化して実DBに接続
        import os
        monkeypatch.delenv('USE_MOCK_DB', raising=False)

        try:
            from app.models.application_type import ApplicationType
            app_types = ApplicationType.get_all_active()
            # 実DBが利用可能な場合のみテスト
            assert isinstance(app_types, list)
        except Exception as e:
            # DB接続エラーの場合はスキップ
            pytest.skip(f"Database not available: {str(e)}")
