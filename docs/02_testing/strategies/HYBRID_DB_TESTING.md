# ハイブリッドDBテスト（マスタ読み取り + トランザクション更新）

## コンセプト

実DBを使いながら安全にテストする方法：

### ✅ マスタテーブル（M_*）
- **読み取りのみ** - 既存のマスタデータを使用
- 更新・削除しない
- 申請種類、ワークフロー定義、ユーザー情報など

### ✅ トランザクションテーブル（T_*）
- **テストデータを作成** - 申請、ワークフローインスタンス
- テスト後に自動削除
- 識別子でテストデータを管理

---

## メリット

1. **実際のマスタデータでテスト** ✅
   - 本番と同じ申請種類定義
   - 実際のワークフロー定義
   - リアルなバリデーションルール

2. **安全にトランザクションをテスト** ✅
   - 既存データを汚染しない
   - テスト後は自動クリーンアップ
   - 失敗しても既存データに影響なし

3. **実用的なカバレッジ向上** ✅
   - 実際のModels層コードが実行される
   - 実際のSQL文が実行される
   - カバレッジ: 23% → 40-50%に向上

---

## 実装方法

### ステップ1: テストデータの識別

テストで作成するデータには識別子を付ける：

```python
# テストデータの命名規則
TEST_USER_PREFIX = 'test_'
TEST_SHOZOKU = '9999999'  # テスト用所属コード

# 例
applicant_user_id = 'test_regression_001'
applicant_shozoku = '9999999'
application_title = '[TEST] Gmailグループ作成テスト'
```

### ステップ2: フィクスチャでクリーンアップ

```python
# conftest.py に追加

import pytest
from app.utils.db import get_db_connection

# テスト用所属コード（マスタに存在しない架空の所属）
TEST_SHOZOKU = '9999999'
TEST_USER_PREFIX = 'test_'

@pytest.fixture(scope='function')
def hybrid_db_session():
    """
    ハイブリッドDBセッション
    - マスタテーブル（M_*）: 読み取りのみ
    - トランザクションテーブル（T_*）: 作成・削除
    """
    # Mock DBを無効化して実DBに接続
    import os
    os.environ.pop('USE_MOCK_DB', None)
    
    # テストで作成したデータのIDを記録
    created_data = {
        'applications': [],
        'workflows': [],
        'approvals': []
    }
    
    yield created_data
    
    # クリーンアップ: テスト後にトランザクションデータを削除
    cleanup_test_data(created_data)


def cleanup_test_data(created_data):
    """テストデータのクリーンアップ"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. 承認タスクを削除
        if created_data['approvals']:
            cursor.execute("""
                DELETE FROM T_WORKFLOW_NODE_APPROVER 
                WHERE node_instance_id IN (
                    SELECT node_instance_id FROM T_WORKFLOW_NODE_INSTANCE
                    WHERE workflow_instance_id IN ({})
                )
            """.format(','.join(str(wf_id) for wf_id in created_data['workflows'])))
        
        # 2. ワークフローノードインスタンスを削除
        if created_data['workflows']:
            cursor.execute("""
                DELETE FROM T_WORKFLOW_NODE_INSTANCE 
                WHERE workflow_instance_id IN ({})
            """.format(','.join(str(wf_id) for wf_id in created_data['workflows'])))
        
        # 3. ワークフローインスタンスを削除
        if created_data['workflows']:
            cursor.execute("""
                DELETE FROM T_WORKFLOW_INSTANCE 
                WHERE workflow_instance_id IN ({})
            """.format(','.join(str(wf_id) for wf_id in created_data['workflows'])))
        
        # 4. 申請詳細を削除
        if created_data['applications']:
            cursor.execute("""
                DELETE FROM T_APPLICATION_DETAIL 
                WHERE application_id IN ({})
            """.format(','.join(str(app_id) for app_id in created_data['applications'])))
        
        # 5. 申請を削除
        if created_data['applications']:
            cursor.execute("""
                DELETE FROM T_APPLICATION 
                WHERE application_id IN ({})
            """.format(','.join(str(app_id) for app_id in created_data['applications'])))
        
        conn.commit()
        print(f"✅ クリーンアップ完了: 申請{len(created_data['applications'])}件、ワークフロー{len(created_data['workflows'])}件")
    
    except Exception as e:
        conn.rollback()
        print(f"⚠️ クリーンアップ失敗: {e}")
    finally:
        cursor.close()
        conn.close()


@pytest.fixture(scope='function')
def test_application_id(hybrid_db_session):
    """テスト用申請を作成し、終了後に削除"""
    from app.models.application import Application
    
    # テスト用申請を作成
    app_id = Application.create({
        'application_type_id': 1,  # 実際のマスタデータから取得
        'action_type': 'create',
        'applicant_user_id': 'test_hybrid_user',
        'applicant_shozoku': TEST_SHOZOKU,
        'jurisdiction_shozoku': TEST_SHOZOKU,
        'application_title': '[TEST] ハイブリッドテスト',
        'remarks': 'このデータは自動削除されます'
    })
    
    # クリーンアップ用に記録
    hybrid_db_session['applications'].append(app_id)
    
    yield app_id
    
    # クリーンアップは hybrid_db_session が自動実行
```

---

## テストコード例

### 例1: マスタデータを使った申請作成テスト

```python
import pytest

@pytest.mark.hybrid_db
@pytest.mark.slow
class TestHybridApplicationFlow:
    """ハイブリッドDBテスト: マスタ読み取り + トランザクション作成"""
    
    def test_create_application_with_real_master(self, hybrid_db_session):
        """実際のマスタデータを使って申請を作成"""
        from app.models.application_type import ApplicationType
        from app.models.application import Application
        from app.models.application_detail import ApplicationDetail
        
        # 1. マスタデータから申請種類を取得（読み取りのみ）
        app_types = ApplicationType.get_all_active()
        assert len(app_types) > 0, "マスタに申請種類が存在しません"
        
        app_type = app_types[0]  # 最初の申請種類を使用
        print(f"✅ マスタから取得: {app_type['application_type_name']}")
        
        # 2. トランザクションデータを作成
        app_id = Application.create({
            'application_type_id': app_type['application_type_id'],
            'action_type': 'create',
            'applicant_user_id': 'test_hybrid_001',
            'applicant_shozoku': '9999999',  # テスト用所属
            'jurisdiction_shozoku': '9999999',
            'application_title': f"[TEST] {app_type['application_type_name']}",
            'remarks': 'ハイブリッドDBテスト'
        })
        
        # クリーンアップ用に記録
        hybrid_db_session['applications'].append(app_id)
        
        assert app_id > 0
        print(f"✅ 申請作成: application_id={app_id}")
        
        # 3. 作成した申請を取得して確認
        app = Application.get_by_id(app_id)
        assert app is not None
        assert app['application_title'].startswith('[TEST]')
        
        # テスト終了後、自動的に削除される
    
    def test_workflow_with_real_definition(self, hybrid_db_session):
        """実際のワークフロー定義を使ってインスタンスを作成"""
        from app.models.workflow import WorkflowDefinition, WorkflowInstance
        from app.models.application import Application
        
        # 1. マスタから申請種類とワークフロー定義を取得
        from app.models.application_type import ApplicationType
        app_type = ApplicationType.get_by_id(1)
        assert app_type is not None
        
        workflow_def_id = app_type['workflow_definition_id']
        print(f"✅ ワークフロー定義ID: {workflow_def_id}")
        
        # 2. ワークフロー定義のノードを取得（読み取りのみ）
        nodes = WorkflowDefinition.get_nodes(workflow_def_id)
        assert len(nodes) > 0, "ワークフロー定義にノードが存在しません"
        print(f"✅ ノード数: {len(nodes)}件")
        
        # 3. テスト用申請を作成
        app_id = Application.create({
            'application_type_id': 1,
            'action_type': 'create',
            'applicant_user_id': 'test_workflow_001',
            'applicant_shozoku': '9999999',
            'jurisdiction_shozoku': '9999999',
            'application_title': '[TEST] ワークフローテスト',
            'remarks': 'テストデータ'
        })
        hybrid_db_session['applications'].append(app_id)
        
        # 4. ワークフローインスタンスを作成（トランザクションテーブル）
        workflow_instance_id = WorkflowInstance.create({
            'workflow_definition_id': workflow_def_id,
            'application_id': app_id,
            'workflow_status': 'in_progress'
        })
        hybrid_db_session['workflows'].append(workflow_instance_id)
        
        assert workflow_instance_id > 0
        print(f"✅ ワークフローインスタンス作成: {workflow_instance_id}")
        
        # テスト終了後、自動削除
```

### 例2: 実際のフィールド定義を使った申請詳細テスト

```python
@pytest.mark.hybrid_db
def test_application_detail_with_real_fields(hybrid_db_session):
    """実際のフィールド定義を使って申請詳細を作成"""
    from app.models.application_field import ApplicationField
    from app.models.application import Application
    from app.models.application_detail import ApplicationDetail
    
    # 1. マスタからフィールド定義を取得
    fields = ApplicationField.get_by_application_type(1)
    assert len(fields) > 0, "フィールド定義が存在しません"
    print(f"✅ フィールド数: {len(fields)}件")
    
    # 2. テスト用申請を作成
    app_id = Application.create({
        'application_type_id': 1,
        'action_type': 'create',
        'applicant_user_id': 'test_detail_001',
        'applicant_shozoku': '9999999',
        'jurisdiction_shozoku': '9999999',
        'application_title': '[TEST] フィールドテスト',
        'remarks': 'テストデータ'
    })
    hybrid_db_session['applications'].append(app_id)
    
    # 3. 各フィールドのテストデータを作成
    details = []
    for field in fields[:3]:  # 最初の3フィールドのみテスト
        details.append({
            'field_id': field['field_id'],
            'field_value': f"test_value_{field['field_id']}"
        })
    
    # 4. 申請詳細を作成
    success = ApplicationDetail.create_bulk(app_id, details)
    assert success
    
    # 5. 作成した詳細を取得
    saved_details = ApplicationDetail.get_by_application(app_id)
    assert len(saved_details) == len(details)
    
    # テスト終了後、自動削除
```

---

## 実行方法

### pytest設定にマーカーを追加

`pytest.ini` に追加：

```ini
markers =
    hybrid_db: ハイブリッドDBテスト（マスタ読み取り + トランザクション更新）
```

### テスト実行

```bash
# ハイブリッドDBテストのみ実行
pytest -m hybrid_db --cov=app --cov-report=html -v

# 詳細ログ付きで実行
pytest -m hybrid_db --cov=app --cov-report=html -v -s
```

---

## 安全性の確認

### テスト前チェックリスト

✅ **実行前に確認**:

1. **マスタデータのバックアップ**（念のため）
2. **テスト用所属コードが実在しない**ことを確認
   ```sql
   SELECT * FROM e_imdb2_users WHERE shozoku = '9999999';
   -- 結果が0件であることを確認
   ```
3. **テスト環境のDB接続情報**を確認
   ```bash
   echo $ORACLE_DSN
   # 本番DBでないことを確認
   ```

### テスト後の確認

```sql
-- テストデータが残っていないか確認
SELECT * FROM T_APPLICATION 
WHERE applicant_user_id LIKE 'test_%' 
   OR applicant_shozoku = '9999999';
-- 結果が0件であることを確認（クリーンアップ成功）
```

---

## トラブルシューティング

### クリーンアップが失敗する場合

手動でテストデータを削除：

```sql
-- テストデータを手動削除
DELETE FROM T_WORKFLOW_NODE_APPROVER 
WHERE node_instance_id IN (
    SELECT node_instance_id FROM T_WORKFLOW_NODE_INSTANCE
    WHERE workflow_instance_id IN (
        SELECT workflow_instance_id FROM T_WORKFLOW_INSTANCE
        WHERE application_id IN (
            SELECT application_id FROM T_APPLICATION
            WHERE applicant_shozoku = '9999999'
        )
    )
);

DELETE FROM T_WORKFLOW_NODE_INSTANCE 
WHERE workflow_instance_id IN (
    SELECT workflow_instance_id FROM T_WORKFLOW_INSTANCE
    WHERE application_id IN (
        SELECT application_id FROM T_APPLICATION
        WHERE applicant_shozoku = '9999999'
    )
);

DELETE FROM T_WORKFLOW_INSTANCE 
WHERE application_id IN (
    SELECT application_id FROM T_APPLICATION
    WHERE applicant_shozoku = '9999999'
);

DELETE FROM T_APPLICATION_DETAIL 
WHERE application_id IN (
    SELECT application_id FROM T_APPLICATION
    WHERE applicant_shozoku = '9999999'
);

DELETE FROM T_APPLICATION 
WHERE applicant_shozoku = '9999999' OR applicant_user_id LIKE 'test_%';

COMMIT;
```

---

## カバレッジの期待値

このアプローチによるカバレッジ向上：

| レイヤー | Mock DB | ハイブリッドDB |
|---------|---------|--------------|
| **Routes層** | 10-20% | 30-40% |
| **Models層** | 20-30% | 60-70% |
| **Services層** | 15-25% | 40-50% |
| **全体** | 23% | 40-50% |

---

## まとめ

### ✅ このアプローチの利点

1. **実際のマスタデータでテスト**
   - 本番と同じ申請種類、ワークフロー定義
   - リアルなテストシナリオ

2. **安全性**
   - マスタテーブルは更新しない
   - トランザクションデータは自動削除
   - 既存データを汚染しない

3. **カバレッジ向上**
   - 23% → 40-50%に向上
   - 実際のModels層コードを実行

4. **実用性**
   - 開発環境のDBをそのまま使える
   - テスト専用DBの準備不要

### 🎯 推奨運用

- **日常開発**: Mock DBテスト
- **週次確認**: ハイブリッドDBテスト（この方法）
- **リリース前**: 完全な統合テスト

この方法なら、実DBを安全に使いながら実用的なテストができます！
