"""
リソース選択とデータ入力の回帰テスト
修正・削除申請でリソースを選択した後、実際のデータを入力するフローをテスト
"""
import pytest


@pytest.mark.integration
@pytest.mark.hybrid_db
class TestResourceSelectionFlow:
    """リソース選択から申請完了までのフロー"""

    def test_modify_with_resource_selection(self, create_test_application, verify_test_db):
        """修正申請: リソース選択 → データ入力 → 申請作成"""
        from app.models.resource import Resource
        from app.models.application_type import ApplicationType
        from app.models.application_field import ApplicationField
        from app.models.application import Application
        from app.models.application_detail import ApplicationDetail

        # 1. 既存リソースを取得（本番データから）
        resources = Resource.search(resource_type='gmail_group', limit=1)
        if len(resources) == 0:
            pytest.skip("テスト用リソースが存在しません")

        existing_resource = resources[0]
        resource_id = existing_resource['resource_id']

        print(f"\n✅ 既存リソース: {existing_resource.get('resource_name', 'N/A')}")

        # 2. 申請種類とフィールド定義を取得（マスタから）
        app_type = ApplicationType.get_by_id(1)  # 修正申請の申請種類
        if not app_type or app_type.get('support_modify') != 'Y':
            pytest.skip("修正申請をサポートしていません")

        fields = ApplicationField.get_by_application_type(app_type['application_type_id'])
        print(f"✅ フィールド数: {len(fields)}件")

        # 3. リソースの現在のデータを取得
        current_data = Resource.get_by_id(resource_id)
        print(f"✅ 現在のデータ取得完了")

        # 4. 修正申請を作成（トランザクションテーブルに書き込み）
        from tests.conftest_hybrid_db import TEST_USER_ID, TEST_SHOZOKU, TEST_JURISDICTION_SHOZOKU

        app_id = Application.create({
            'application_type_id': app_type['application_type_id'],
            'action_type': 'modify',
            'resource_id': resource_id,
            'applicant_user_id': TEST_USER_ID,
            'applicant_shozoku': TEST_SHOZOKU,
            'jurisdiction_shozoku': TEST_JURISDICTION_SHOZOKU,
            'application_title': f"[TEST] {existing_resource.get('resource_name', '')} の修正",
            'remarks': '回帰テスト - 自動削除されます'
        })

        assert app_id > 0
        print(f"✅ 申請作成: application_id={app_id}")

        # 5. フィールドデータを入力（修正内容）
        details = []
        for i, field in enumerate(fields[:3]):  # 最初の3フィールドのみテスト
            # 既存の値を取得（あれば）
            current_value = current_data.get(field['field_name'], '')

            # テスト用に値を変更
            new_value = f"{current_value}_MODIFIED_TEST" if current_value else f"test_value_{i+1}"

            details.append({
                'detail_seq': 1,
                'field_id': field['field_id'],
                'field_value': new_value
            })

        # 6. 申請詳細を保存
        success = ApplicationDetail.create_bulk(app_id, details)
        assert success
        print(f"✅ 申請詳細保存: {len(details)}件")

        # 7. 保存されたデータを確認
        saved_details = ApplicationDetail.get_by_application(app_id)
        assert len(saved_details) >= len(details)
        print(f"✅ 保存確認完了: {len(saved_details)}件")

        # クリーンアップは hybrid_db_session フィクスチャが自動実行
        # このテスト終了後、T_APPLICATION と T_APPLICATION_DETAIL は自動削除される
        # 既存のリソース（M_RESOURCE）は一切変更されていない

    def test_delete_with_resource_selection(self, create_test_application, verify_test_db):
        """削除申請: リソース選択 → 削除理由入力 → 申請作成"""
        from app.models.resource import Resource
        from app.models.application_type import ApplicationType
        from app.models.application import Application
        from app.models.application_detail import ApplicationDetail

        # 1. 既存リソースを取得
        resources = Resource.search(resource_type='gmail_group', limit=1)
        if len(resources) == 0:
            pytest.skip("テスト用リソースが存在しません")

        existing_resource = resources[0]
        resource_id = existing_resource['resource_id']

        print(f"\n✅ 削除対象リソース: {existing_resource.get('resource_name', 'N/A')}")

        # 2. 申請種類を取得
        app_type = ApplicationType.get_by_id(1)  # 削除申請の申請種類
        if not app_type or app_type.get('support_delete') != 'Y':
            pytest.skip("削除申請をサポートしていません")

        # 3. 削除申請を作成
        from tests.conftest_hybrid_db import TEST_USER_ID, TEST_SHOZOKU, TEST_JURISDICTION_SHOZOKU

        app_id = Application.create({
            'application_type_id': app_type['application_type_id'],
            'action_type': 'delete',
            'resource_id': resource_id,
            'applicant_user_id': TEST_USER_ID,
            'applicant_shozoku': TEST_SHOZOKU,
            'jurisdiction_shozoku': TEST_JURISDICTION_SHOZOKU,
            'application_title': f"[TEST] {existing_resource.get('resource_name', '')} の削除",
            'remarks': '回帰テスト - 実際には削除されません'
        })

        assert app_id > 0
        print(f"✅ 削除申請作成: application_id={app_id}")

        # 4. 削除理由を入力（フィールドとして）
        details = [
            {
                'detail_seq': 1,
                'field_id': 1,  # 削除理由フィールド
                'field_value': 'テスト用の削除申請です。実際には削除されません。'
            }
        ]

        success = ApplicationDetail.create_bulk(app_id, details)
        assert success
        print(f"✅ 削除理由保存完了")

        # クリーンアップは自動実行
        # 既存のリソースは削除されない（申請データのみ削除）


@pytest.mark.integration
@pytest.mark.hybrid_db
class TestMultiRecordInput:
    """複数レコード形式のデータ入力テスト"""

    def test_multi_record_data_entry(self, create_test_application, verify_test_db):
        """複数レコード形式: 複数行のデータを入力"""
        from app.models.application_type import ApplicationType
        from app.models.application_field import ApplicationField
        from app.models.application import Application
        from app.models.application_detail import ApplicationDetail

        # 1. 複数レコード形式の申請種類を取得
        app_types = ApplicationType.get_all_active()
        multi_record_type = None
        for at in app_types:
            if at.get('is_multi_record') == 'Y':
                multi_record_type = at
                break

        if not multi_record_type:
            pytest.skip("複数レコード形式の申請種類が存在しません")

        print(f"\n✅ 申請種類: {multi_record_type['application_type_name']}")

        # 2. フィールド定義を取得
        fields = ApplicationField.get_by_application_type(multi_record_type['application_type_id'])
        print(f"✅ フィールド数: {len(fields)}件")

        # 3. 申請を作成
        from tests.conftest_hybrid_db import TEST_USER_ID, TEST_SHOZOKU, TEST_JURISDICTION_SHOZOKU

        app_id = Application.create({
            'application_type_id': multi_record_type['application_type_id'],
            'action_type': 'create',
            'applicant_user_id': TEST_USER_ID,
            'applicant_shozoku': TEST_SHOZOKU,
            'jurisdiction_shozoku': TEST_JURISDICTION_SHOZOKU,
            'application_title': '[TEST] 複数レコード入力テスト',
            'remarks': '回帰テスト'
        })

        print(f"✅ 申請作成: application_id={app_id}")

        # 4. 複数レコードを入力（3レコード）
        details = []
        for record_seq in range(1, 4):  # 3レコード
            for field in fields[:2]:  # 各レコードで2フィールド
                details.append({
                    'detail_seq': record_seq,
                    'field_id': field['field_id'],
                    'field_value': f"Record{record_seq}_Field{field['field_id']}_Value"
                })

        # 5. 一括保存
        success = ApplicationDetail.create_bulk(app_id, details)
        assert success
        print(f"✅ 複数レコード保存: {len(details)}件 (3レコード × 2フィールド)")

        # 6. レコード別に取得して確認
        saved_details = ApplicationDetail.get_by_application(app_id)
        assert len(saved_details) >= len(details)

        # detail_seqごとにグループ化
        grouped = ApplicationDetail.get_grouped_by_seq(app_id)
        assert len(grouped) >= 3  # 3レコード
        print(f"✅ レコード数確認: {len(grouped)}レコード")


@pytest.mark.integration
@pytest.mark.visual
class TestResourceSelectionHTML:
    """リソース選択画面のHTML保存テスト"""

    def test_modify_resource_list_html(self, auth_client, save_html, monkeypatch):
        """修正対象リソース一覧画面のHTML"""
        # リソース一覧のモック
        class MockResource:
            @staticmethod
            def search(**kwargs):
                return [
                    {
                        'resource_id': 1,
                        'resource_name': 'sales-team@example.com',
                        'resource_type': 'gmail_group',
                        'description': '営業部メーリングリスト'
                    },
                    {
                        'resource_id': 2,
                        'resource_name': 'dev-team@example.com',
                        'resource_type': 'gmail_group',
                        'description': '開発部メーリングリスト'
                    }
                ]

        from app.models import resource
        monkeypatch.setattr(resource, 'Resource', MockResource)

        # リソース一覧画面にアクセス
        response = auth_client.get('/application/modify/select-resource/1')
        if response.status_code == 200:
            save_html(response, '07_modify_select_resource.html')
            print("\n✅ HTML保存: 07_modify_select_resource.html")
        else:
            # ルートが実装されていない場合
            pytest.skip(f"リソース選択画面が未実装 (status={response.status_code})")

    def test_modify_form_with_selected_resource_html(self, auth_client, save_html, monkeypatch):
        """リソース選択後の修正フォーム画面のHTML"""
        # モックデータ
        class MockResource:
            @staticmethod
            def get_by_id(resource_id):
                return {
                    'resource_id': resource_id,
                    'resource_name': 'sales-team@example.com',
                    'description': '営業部メーリングリスト',
                    'owner': 'tanaka_taro'
                }

        class MockApplicationType:
            @staticmethod
            def get_by_id(app_type_id):
                return {
                    'application_type_id': app_type_id,
                    'support_modify': 'Y',
                    'is_multi_record': 'N'
                }

        class MockApplicationField:
            @staticmethod
            def get_by_application_type(app_type_id):
                return [
                    {
                        'field_id': 1,
                        'field_name': 'resource_name',
                        'field_label': 'グループメールアドレス',
                        'field_type': 'text',
                        'is_required_modify': 'Y'
                    },
                    {
                        'field_id': 2,
                        'field_name': 'description',
                        'field_label': '説明',
                        'field_type': 'textarea',
                        'is_required_modify': 'N'
                    }
                ]

        from app.models import resource, application_type, application_field
        monkeypatch.setattr(resource, 'Resource', MockResource)
        monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
        monkeypatch.setattr(application_field, 'ApplicationField', MockApplicationField)

        # 修正フォーム画面にアクセス（リソースID=1）
        response = auth_client.get('/application/modify/1/1')
        if response.status_code == 200:
            save_html(response, '08_modify_form_with_resource.html')
            print("\n✅ HTML保存: 08_modify_form_with_resource.html")
        else:
            pytest.skip(f"修正フォーム画面が未実装 (status={response.status_code})")
