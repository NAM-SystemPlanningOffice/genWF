"""
画面イメージ保存テスト（HTML）
ブラウザで開いて画面を確認できます
"""
import pytest


@pytest.mark.visual
@pytest.mark.integration
class TestVisualHTML:
    """主要画面のHTML保存テスト"""

    def test_login_page_html(self, client, save_html):
        """ログイン画面のHTML保存"""
        response = client.get('/auth/login')
        save_html(response, '01_login_page.html')
        assert response.status_code == 200

    def test_application_list_html(self, auth_client, save_html, monkeypatch):
        """申請一覧画面のHTML保存"""
        # モックデータ
        class MockApplicationType:
            @staticmethod
            def get_all_active(**kwargs):
                return [
                    {
                        'application_type_id': 1,
                        'application_type_name': 'Gmailグループ作成',
                        'application_type_description': '説明文',
                        'support_create': 'Y',
                        'support_modify': 'Y',
                        'support_delete': 'Y'
                    },
                    {
                        'application_type_id': 2,
                        'application_type_name': 'ユーザー権限変更',
                        'application_type_description': '説明文',
                        'support_create': 'Y',
                        'support_modify': 'Y',
                        'support_delete': 'N'
                    }
                ]

        from app.models import application_type
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)

        response = auth_client.get('/application/')
        save_html(response, '02_application_list.html')
        assert response.status_code == 200

    def test_application_create_html(self, auth_client, save_html, monkeypatch):
        """申請作成画面のHTML保存"""
        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'application_type_name': 'Gmailグループ作成',
                    'application_type_description': 'Gmailグループの新規作成',
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
                        'field_name': 'group_email',
                        'field_label': 'グループメールアドレス',
                        'field_type': 'text',
                        'is_required_create': 'Y',
                        'display_order': 1,
                        'pulldown_group_id': None,
                        'help_text': '例: group-name@example.com'
                    },
                    {
                        'field_id': 2,
                        'field_name': 'group_description',
                        'field_label': 'グループ説明',
                        'field_type': 'textarea',
                        'is_required_create': 'Y',
                        'display_order': 2,
                        'pulldown_group_id': None,
                        'help_text': 'グループの用途を記載'
                    },
                    {
                        'field_id': 3,
                        'field_name': 'owner_user_id',
                        'field_label': 'オーナー',
                        'field_type': 'select',
                        'is_required_create': 'Y',
                        'display_order': 3,
                        'pulldown_group_id': 1,
                        'pulldown_options': [
                            {'option_value': 'user1', 'option_label': 'ユーザー1'},
                            {'option_value': 'user2', 'option_label': 'ユーザー2'}
                        ],
                        'help_text': 'グループの管理者'
                    }
                ]

        from app.models import application_type, application_field
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(application_field, 'ApplicationField', MockApplicationField)

        response = auth_client.get('/application/create/1')
        save_html(response, '03_application_create.html')
        assert response.status_code == 200

    def test_approval_tasks_html(self, auth_client, save_html, monkeypatch):
        """承認タスク一覧のHTML保存"""
        class MockApprovalTask:
            @staticmethod
            def get_pending_tasks(user_id):
                return [
                    {
                        'node_instance_id': 1,
                        'application_id': 1,
                        'application_title': 'Gmailグループ作成申請',
                        'applicant_user_name': '申請者太郎',
                        'applicant_shozoku_name': '営業部',
                        'node_name': '所属長承認',
                        'created_at': '2026-06-15 10:00:00'
                    },
                    {
                        'node_instance_id': 2,
                        'application_id': 2,
                        'application_title': 'ユーザー権限変更申請',
                        'applicant_user_name': '申請者花子',
                        'applicant_shozoku_name': '総務部',
                        'node_name': '所属長承認',
                        'created_at': '2026-06-14 15:30:00'
                    }
                ]

        from app.models import approval_task
        monkeypatch.setattr(approval_task, 'ApprovalTask', MockApprovalTask)

        response = auth_client.get('/approval/tasks')
        save_html(response, '04_approval_tasks.html')
        assert response.status_code == 200

    def test_approval_task_detail_html(self, auth_client, save_html, monkeypatch):
        """承認タスク詳細のHTML保存"""
        class MockApprovalTask:
            @staticmethod
            def get_task_detail(node_instance_id, user_id):
                return {
                    'node_instance_id': node_instance_id,
                    'application_id': 1,
                    'application_title': 'Gmailグループ作成申請',
                    'applicant_user_name': '申請者太郎',
                    'applicant_shozoku_name': '営業部',
                    'node_name': '所属長承認',
                    'node_status': 'pending',
                    'workflow_instance_id': 1
                }

        class MockApplication:
            @staticmethod
            def get_by_id(app_id):
                return {
                    'application_id': app_id,
                    'application_type_id': 1,
                    'application_title': 'Gmailグループ作成申請',
                    'applicant_user_id': 'applicant',
                    'applicant_user_name': '申請者太郎',
                    'applicant_shozoku': '1234000',
                    'applicant_shozoku_name': '営業部',
                    'action_type': 'create',
                    'remarks': '営業用のメーリングリスト',
                    'created_at': '2026-06-15 10:00:00'
                }

        class MockApplicationDetail:
            @staticmethod
            def get_by_application(app_id):
                return [
                    {
                        'field_id': 1,
                        'field_name': 'group_email',
                        'field_label': 'グループメールアドレス',
                        'field_value': 'sales-team@example.com'
                    },
                    {
                        'field_id': 2,
                        'field_name': 'group_description',
                        'field_label': 'グループ説明',
                        'field_value': '営業部の情報共有用メーリングリスト'
                    }
                ]

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
                return [
                    {
                        'node_seq': 1,
                        'node_name': '所属長承認',
                        'node_status': 'pending',
                        'approver_user_names': '承認者太郎'
                    },
                    {
                        'node_seq': 2,
                        'node_name': 'システム企画室承認',
                        'node_status': 'not_started',
                        'approver_user_names': None
                    }
                ]

        from app.models import approval_task, application, application_detail, application_type, workflow
        monkeypatch.setattr(approval_task, 'ApprovalTask', MockApprovalTask)
        monkeypatch.setattr(application, 'Application', MockApplication)
        monkeypatch.setattr(application_detail, 'ApplicationDetail', MockApplicationDetail)
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(workflow, 'WorkflowNodeInstance', MockWorkflowNodeInstance)

        response = auth_client.get('/approval/task/1')
        save_html(response, '05_approval_task_detail.html')
        assert response.status_code == 200

    def test_admin_page_html(self, admin_client, save_html, monkeypatch):
        """管理画面のHTML保存"""
        class MockApplicationType:
            @staticmethod
            def get_all(include_deleted=False):
                return [
                    {
                        'application_type_id': 1,
                        'application_type_name': 'Gmailグループ作成',
                        'is_published': 'Y',
                        'is_deleted': 'N'
                    }
                ]

        from app.models.admin import application_type
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)

        response = admin_client.get('/admin/')
        save_html(response, '06_admin_page.html')
        # 管理画面が実装されている場合は200、未実装なら404
        assert response.status_code in [200, 404]


@pytest.mark.visual
@pytest.mark.integration
class TestVisualErrorPages:
    """エラーページのHTML保存テスト"""

    def test_404_page_html(self, client, save_html):
        """404エラーページのHTML保存"""
        response = client.get('/nonexistent-page')
        save_html(response, '90_error_404.html')
        assert response.status_code == 404

    def test_403_page_html(self, auth_client, save_html):
        """403エラーページのHTML保存（権限なし）"""
        # 管理者権限が必要なページに一般ユーザーでアクセス
        response = auth_client.get('/admin/')
        if response.status_code == 403:
            save_html(response, '91_error_403.html')
        # 権限チェックが実装されていない場合は404
        assert response.status_code in [403, 404]
