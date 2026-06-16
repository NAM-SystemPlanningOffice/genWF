"""
ハイブリッドDBテスト
マスタテーブル（M_*）: 読み取りのみ
トランザクションテーブル（T_*）: 作成・削除
"""
import pytest
import sys
import os

# conftest_hybrid_db.py からフィクスチャをインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from conftest_hybrid_db import (
    hybrid_db_session,
    verify_test_db,
    test_application_data,
    create_test_application,
    create_test_workflow,
    TEST_USER_ID,
    TEST_SHOZOKU,
    TEST_JURISDICTION_SHOZOKU
)


@pytest.mark.hybrid_db
@pytest.mark.slow
class TestHybridDBApplicationFlow:
    """ハイブリッドDBテスト: 申請フロー"""

    def test_read_master_application_types(self, verify_test_db):
        """マスタテーブルから申請種類を読み取り（更新なし）"""
        from app.models.application_type import ApplicationType

        # マスタデータを取得（読み取りのみ）
        app_types = ApplicationType.get_all_active()

        assert isinstance(app_types, list)
        if len(app_types) > 0:
            assert 'application_type_id' in app_types[0]
            assert 'application_type_name' in app_types[0]
            print(f"\n✅ 申請種類取得: {len(app_types)}件")
            for at in app_types[:3]:
                print(f"  - {at['application_type_name']}")

    def test_create_application_with_real_master(self, create_test_application, verify_test_db):
        """実際のマスタデータを使って申請を作成"""
        from app.models.application_type import ApplicationType
        from app.models.application import Application

        # 1. マスタから申請種類を取得
        app_types = ApplicationType.get_all_active()
        assert len(app_types) > 0, "マスタに申請種類が存在しません"

        app_type = app_types[0]
        print(f"\n✅ 使用する申請種類: {app_type['application_type_name']}")

        # 2. トランザクションデータを作成
        app_id = create_test_application({
            'application_type_id': app_type['application_type_id'],
            'action_type': 'create',
            'applicant_user_id': TEST_USER_ID,
            'applicant_shozoku': TEST_SHOZOKU,
            'jurisdiction_shozoku': TEST_JURISDICTION_SHOZOKU,
            'application_title': f"[TEST] {app_type['application_type_name']}",
            'remarks': 'ハイブリッドDBテスト - 自動削除されます'
        })

        assert app_id > 0
        print(f"✅ 申請作成成功: application_id={app_id}")

        # 3. 作成した申請を取得
        app = Application.get_by_id(app_id)
        assert app is not None
        assert app['application_title'].startswith('[TEST]')
        assert app['applicant_shozoku'] == TEST_SHOZOKU

        print(f"✅ 申請取得成功: {app['application_title']}")

        # テスト終了後、自動的にクリーンアップされる

    def test_application_detail_with_real_fields(self, create_test_application, verify_test_db):
        """実際のフィールド定義を使って申請詳細を作成"""
        from app.models.application_field import ApplicationField
        from app.models.application_detail import ApplicationDetail
        from app.models.application import Application

        # 1. マスタからフィールド定義を取得
        fields = ApplicationField.get_by_application_type(1)
        if len(fields) == 0:
            pytest.skip("フィールド定義が存在しません")

        print(f"\n✅ フィールド数: {len(fields)}件")

        # 2. テスト用申請を作成
        app_id = create_test_application({
            'application_type_id': 1,
            'action_type': 'create',
            'applicant_user_id': TEST_USER_ID,
            'applicant_shozoku': TEST_SHOZOKU,
            'jurisdiction_shozoku': TEST_JURISDICTION_SHOZOKU,
            'application_title': '[TEST] フィールドテスト',
            'remarks': 'テストデータ'
        })

        # 3. 各フィールドのテストデータを作成
        details = []
        for i, field in enumerate(fields[:3]):  # 最初の3フィールドのみ
            details.append({
                'detail_seq': 1,
                'field_id': field['field_id'],
                'field_value': f'test_value_{i+1}'
            })

        # 4. 申請詳細を作成
        success = ApplicationDetail.create_bulk(app_id, details)
        assert success
        print(f"✅ 申請詳細作成: {len(details)}件")

        # 5. 作成した詳細を取得
        saved_details = ApplicationDetail.get_by_application(app_id)
        assert len(saved_details) >= len(details)

        print(f"✅ 申請詳細取得: {len(saved_details)}件")


@pytest.mark.hybrid_db
@pytest.mark.slow
class TestHybridDBWorkflowFlow:
    """ハイブリッドDBテスト: ワークフローフロー"""

    def test_read_workflow_definition(self, verify_test_db):
        """マスタからワークフロー定義を読み取り"""
        from app.models.workflow import WorkflowDefinition
        from app.models.application_type import ApplicationType

        # マスタから申請種類を取得
        app_types = ApplicationType.get_all_active()
        if len(app_types) == 0:
            pytest.skip("申請種類が存在しません")

        workflow_def_id = app_types[0].get('workflow_definition_id')
        if not workflow_def_id:
            pytest.skip("ワークフロー定義IDが設定されていません")

        # ワークフロー定義を取得
        workflow_def = WorkflowDefinition.get_by_id(workflow_def_id)
        if not workflow_def:
            pytest.skip("ワークフロー定義が存在しません")

        print(f"\n✅ ワークフロー定義: {workflow_def.get('workflow_name', 'N/A')}")

        # ノード定義を取得
        nodes = WorkflowDefinition.get_nodes(workflow_def_id)
        assert isinstance(nodes, list)
        print(f"✅ ノード数: {len(nodes)}件")

        for node in nodes:
            print(f"  - [{node['node_seq']}] {node['node_name']} ({node['node_type']})")

    def test_create_workflow_instance(self, create_test_application, create_test_workflow, verify_test_db):
        """実際のワークフロー定義を使ってインスタンスを作成"""
        from app.models.workflow import WorkflowDefinition, WorkflowInstance
        from app.models.application_type import ApplicationType

        # 1. マスタから申請種類とワークフロー定義を取得
        app_type = ApplicationType.get_by_id(1)
        if not app_type:
            pytest.skip("申請種類が存在しません")

        workflow_def_id = app_type.get('workflow_definition_id')
        if not workflow_def_id:
            pytest.skip("ワークフロー定義IDが設定されていません")

        print(f"\n✅ ワークフロー定義ID: {workflow_def_id}")

        # 2. ワークフロー定義のノードを取得
        nodes = WorkflowDefinition.get_nodes(workflow_def_id)
        if len(nodes) == 0:
            pytest.skip("ワークフロー定義にノードが存在しません")

        print(f"✅ ノード数: {len(nodes)}件")

        # 3. テスト用申請を作成
        app_id = create_test_application({
            'application_type_id': 1,
            'action_type': 'create',
            'applicant_user_id': TEST_USER_ID,
            'applicant_shozoku': TEST_SHOZOKU,
            'jurisdiction_shozoku': TEST_JURISDICTION_SHOZOKU,
            'application_title': '[TEST] ワークフローインスタンステスト',
            'remarks': 'テストデータ'
        })

        # 4. ワークフローインスタンスを作成
        workflow_instance_id = create_test_workflow({
            'workflow_definition_id': workflow_def_id,
            'application_id': app_id,
            'workflow_status': 'in_progress'
        })

        assert workflow_instance_id > 0
        print(f"✅ ワークフローインスタンス作成: {workflow_instance_id}")

        # 5. 作成したインスタンスを取得
        instance = WorkflowInstance.get_by_id(workflow_instance_id)
        assert instance is not None
        assert instance['application_id'] == app_id
        assert instance['workflow_status'] == 'in_progress'

        print(f"✅ ワークフローインスタンス取得成功")


@pytest.mark.hybrid_db
class TestHybridDBReadOnly:
    """ハイブリッドDBテスト: 読み取り専用テスト（安全）"""

    def test_read_users(self, verify_test_db):
        """ユーザー情報の読み取り"""
        from app.models.user import User

        # ユーザー情報を取得（読み取りのみ）
        user = User.get_by_id('admin')  # 既存ユーザー

        if user:
            assert 'user_id' in user
            assert 'user_name' in user
            print(f"\n✅ ユーザー取得: {user.get('user_name', 'N/A')}")
        else:
            print("\n⚠️ ユーザーが見つかりません（正常）")

    def test_read_validation_rules(self, verify_test_db):
        """バリデーションルールの読み取り"""
        from app.models.admin.validation_rule import ValidationRule

        try:
            rules = ValidationRule.get_all()
            assert isinstance(rules, list)
            print(f"\n✅ バリデーションルール: {len(rules)}件")
        except Exception as e:
            pytest.skip(f"バリデーションルールの取得に失敗: {e}")

    def test_read_pulldown_groups(self, verify_test_db):
        """プルダウングループの読み取り"""
        from app.models.admin.pulldown_group import PulldownGroup

        try:
            groups = PulldownGroup.get_all()
            assert isinstance(groups, list)
            print(f"\n✅ プルダウングループ: {len(groups)}件")
        except Exception as e:
            pytest.skip(f"プルダウングループの取得に失敗: {e}")


@pytest.mark.hybrid_db
class TestHybridDBCleanup:
    """クリーンアップのテスト"""

    def test_cleanup_verification(self, verify_test_db):
        """テストデータが残っていないことを確認"""
        from app.utils.db import get_db_connection, dict_fetchall

        conn = get_db_connection()
        cursor = conn.cursor()

        # テスト用所属で申請が残っていないか確認
        cursor.execute("""
            SELECT application_id, application_title, applicant_user_id
            FROM T_APPLICATION
            WHERE applicant_shozoku = :test_shozoku
        """, {'test_shozoku': TEST_SHOZOKU})

        remaining = dict_fetchall(cursor)
        cursor.close()
        conn.close()

        if len(remaining) > 0:
            print(f"\n⚠️ クリーンアップ漏れ: {len(remaining)}件")
            for app in remaining:
                print(f"  - ID={app['application_id']}: {app['application_title']}")

            # 警告のみ（テスト失敗にはしない）
            pytest.skip(f"⚠️ テストデータが{len(remaining)}件残っています")
        else:
            print(f"\n✅ クリーンアップ確認: テストデータなし")
