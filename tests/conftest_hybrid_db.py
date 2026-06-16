"""
ハイブリッドDBテスト用のフィクスチャ
マスタテーブル（M_*）: 読み取りのみ
トランザクションテーブル（T_*）: 作成・削除
"""
import pytest
import os

# テスト用の識別子（実際に存在するユーザー・所属に変更してください）
TEST_USER_ID = 't3_mori'  # テスト用ユーザーID（実際に存在するユーザーID）
TEST_SHOZOKU = '3030000'  # テスト用所属コード（実際に存在する所属コード）
TEST_JURISDICTION_SHOZOKU = '3030000'  # 所管所属コード（通常は申請者所属と同じ）


@pytest.fixture(scope='function')
def hybrid_db_session():
    """
    ハイブリッドDBセッション
    - Mock DBを無効化して実DBに接続
    - テストで作成したデータを記録
    - テスト終了後に自動クリーンアップ
    """
    # Mock DBを無効化
    original_mock_db = os.environ.get('USE_MOCK_DB')
    if 'USE_MOCK_DB' in os.environ:
        del os.environ['USE_MOCK_DB']

    # テストで作成したデータのIDを記録
    created_data = {
        'applications': [],
        'workflows': [],
        'approval_nodes': []
    }

    yield created_data

    # クリーンアップ: テスト後にトランザクションデータを削除
    cleanup_test_data(created_data)

    # Mock DB設定を復元
    if original_mock_db is not None:
        os.environ['USE_MOCK_DB'] = original_mock_db


def cleanup_test_data(created_data):
    """
    テストデータのクリーンアップ
    トランザクションテーブル（T_*）からテストデータを削除
    """
    from app.utils.db import get_db_connection

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 削除の順序: 外部キー制約を考慮
        # 1. T_WORKFLOW_NODE_APPROVER（承認者）
        if created_data['workflows']:
            workflow_ids = ','.join(str(wf_id) for wf_id in created_data['workflows'])
            try:
                cursor.execute(f"""
                    DELETE FROM T_WORKFLOW_NODE_APPROVER
                    WHERE node_instance_id IN (
                        SELECT node_instance_id FROM T_WORKFLOW_NODE_INSTANCE
                        WHERE workflow_instance_id IN ({workflow_ids})
                    )
                """)
                print(f"✅ 承認者削除: {cursor.rowcount}件")
            except Exception as e:
                print(f"⚠️ 承認者削除エラー: {e}")

        # 2. T_WORKFLOW_NODE_INSTANCE（ワークフローノード）
        if created_data['workflows']:
            workflow_ids = ','.join(str(wf_id) for wf_id in created_data['workflows'])
            try:
                cursor.execute(f"""
                    DELETE FROM T_WORKFLOW_NODE_INSTANCE
                    WHERE workflow_instance_id IN ({workflow_ids})
                """)
                print(f"✅ ワークフローノード削除: {cursor.rowcount}件")
            except Exception as e:
                print(f"⚠️ ワークフローノード削除エラー: {e}")

        # 3. T_WORKFLOW_INSTANCE（ワークフローインスタンス）
        if created_data['workflows']:
            workflow_ids = ','.join(str(wf_id) for wf_id in created_data['workflows'])
            try:
                cursor.execute(f"""
                    DELETE FROM T_WORKFLOW_INSTANCE
                    WHERE workflow_instance_id IN ({workflow_ids})
                """)
                print(f"✅ ワークフローインスタンス削除: {cursor.rowcount}件")
            except Exception as e:
                print(f"⚠️ ワークフローインスタンス削除エラー: {e}")

        # 4. T_APPLICATION_DETAIL（申請詳細）
        if created_data['applications']:
            app_ids = ','.join(str(app_id) for app_id in created_data['applications'])
            try:
                cursor.execute(f"""
                    DELETE FROM T_APPLICATION_DETAIL
                    WHERE application_id IN ({app_ids})
                """)
                print(f"✅ 申請詳細削除: {cursor.rowcount}件")
            except Exception as e:
                print(f"⚠️ 申請詳細削除エラー: {e}")

        # 5. T_APPLICATION（申請）
        if created_data['applications']:
            app_ids = ','.join(str(app_id) for app_id in created_data['applications'])
            try:
                cursor.execute(f"""
                    DELETE FROM T_APPLICATION
                    WHERE application_id IN ({app_ids})
                """)
                print(f"✅ 申請削除: {cursor.rowcount}件")
            except Exception as e:
                print(f"⚠️ 申請削除エラー: {e}")

        # コミット
        conn.commit()

        # サマリー表示
        total = len(created_data['applications']) + len(created_data['workflows'])
        if total > 0:
            print(f"\n✅ クリーンアップ完了: 申請 {len(created_data['applications'])}件、ワークフロー {len(created_data['workflows'])}件")

    except Exception as e:
        print(f"\n⚠️ クリーンアップ失敗: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass

    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


@pytest.fixture(scope='function')
def verify_test_db():
    """
    テスト実行前に実DBであることを確認
    本番DBでないことを確認
    """
    dsn = os.environ.get('ORACLE_DSN', '')

    # 本番DBチェック
    dangerous_keywords = ['production', 'prod', 'prd']
    if any(keyword in dsn.lower() for keyword in dangerous_keywords):
        pytest.exit("⚠️ DANGER: Cannot run hybrid DB tests against production database!")

    # DB接続確認
    if not dsn:
        pytest.skip("⚠️ No database configured - skipping hybrid DB tests")

    print(f"\n✅ DB接続確認: {dsn}")
    return dsn


@pytest.fixture(scope='function')
def test_application_data():
    """テスト用申請データのテンプレート"""
    return {
        'application_type_id': 1,  # 実際のマスタから取得する申請種類ID
        'action_type': 'create',
        'applicant_user_id': TEST_USER_ID,
        'applicant_shozoku': TEST_SHOZOKU,
        'jurisdiction_shozoku': TEST_JURISDICTION_SHOZOKU,
        'application_title': '[TEST] ハイブリッドDBテスト',
        'remarks': 'このデータは自動削除されます'
    }


@pytest.fixture(scope='function')
def create_test_application(hybrid_db_session, verify_test_db):
    """
    テスト用申請を作成するヘルパー
    使用後は自動的にクリーンアップされる
    """
    from app.models.application import Application

    def _create(application_data=None):
        """申請を作成"""
        if application_data is None:
            application_data = {
                'application_type_id': 1,
                'action_type': 'create',
                'applicant_user_id': TEST_USER_ID,
                'applicant_shozoku': TEST_SHOZOKU,
                'jurisdiction_shozoku': TEST_JURISDICTION_SHOZOKU,
                'application_title': '[TEST] Auto Created',
                'remarks': 'Auto cleanup'
            }

        # 申請作成
        app_id = Application.create(application_data)

        # クリーンアップ用に記録
        hybrid_db_session['applications'].append(app_id)

        return app_id

    return _create


@pytest.fixture(scope='function')
def create_test_workflow(hybrid_db_session, verify_test_db):
    """
    テスト用ワークフローインスタンスを作成するヘルパー
    使用後は自動的にクリーンアップされる
    """
    from app.models.workflow import WorkflowInstance

    def _create(workflow_data):
        """ワークフローインスタンスを作成"""
        workflow_id = WorkflowInstance.create(workflow_data)

        # クリーンアップ用に記録
        hybrid_db_session['workflows'].append(workflow_id)

        return workflow_id

    return _create


# テスト用の定数をエクスポート
__all__ = [
    'hybrid_db_session',
    'verify_test_db',
    'test_application_data',
    'create_test_application',
    'create_test_workflow',
    'TEST_USER_ID',
    'TEST_SHOZOKU',
    'TEST_JURISDICTION_SHOZOKU'
]
