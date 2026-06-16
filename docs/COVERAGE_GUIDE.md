# カバレッジ判断ガイド

## 現状のカバレッジ: 23%

このドキュメントでは、0%カバレッジのモジュールをどう判断すべきか説明します。

---

## カバレッジ0%のモジュールの分類と優先順位

### 🔴 優先度: 高（今後テストを追加すべき）

これらは**ビジネスロジックの中核**なので、テストが必要です：

#### 1. **Routes層（画面・API）** - 0%
- `app/routes/admin.py` - 管理画面（申請種類、ワークフロー定義等の管理）
- `app/routes/api.py` - APIエンドポイント
- `app/routes/application_modify.py` - 申請修正画面
- `app/routes/application_multi.py` - 複数レコード申請画面

**判断理由**:
- ユーザーが直接操作する画面なので、**回帰テストで最も重要**
- 現在のテストはモックを使った単体テストのみで、実際のルートハンドラーは呼ばれていない

**対応方法**:
```python
# 実際のルートにアクセスするテストを追加
def test_admin_application_types(admin_client):
    response = admin_client.get('/admin/application-types')
    assert response.status_code == 200
```

#### 2. **Models/Admin層** - 0%
- `app/models/admin/application_field.py`
- `app/models/admin/application_type.py`
- `app/models/admin/field_validation.py`
- `app/models/admin/pulldown_group.py`
- `app/models/admin/pulldown_option.py`
- `app/models/admin/validation_rule.py`
- `app/models/admin/workflow_definition.py`
- `app/models/admin/workflow_node_definition.py`

**判断理由**:
- 管理機能のモデル層
- 申請種類やワークフロー定義の設定データを扱う
- テストではモックを使っているため、実際のコードは実行されていない

**対応方法**:
- 実DBを使った統合テストを追加
- または、admin層の各モデルの単体テストを追加

---

### 🟡 優先度: 中（状況に応じて判断）

#### 3. **Validation/Workflow Services** - 18-26%
- `app/services/validation_service.py` - 18%
- `app/services/workflow_service.py` - 26%

**判断理由**:
- 一部はカバーされているが不十分
- バリデーションやワークフロー制御の重要なロジックを含む

**対応方法**:
- カバーされていない分岐条件やエラーハンドリングのテストを追加

---

### 🟢 優先度: 低（現状のまま許容可能）

#### 4. **設定・初期化ファイル**
- `app/config.py` - 100% ✅
- `app/__init__.py` - 76% ✅
- `app/models/__init__.py` - 100% ✅

**判断理由**:
- 設定値の読み込みや初期化処理のみ
- 既に高いカバレッジを達成

#### 5. **Utils層** - すでに一部カバー済み
- `app/utils/decorators.py` - 18%
- `app/utils/helpers.py` - 39%
- `app/utils/text_formatter.py` - 52%
- `app/utils/windows_auth.py` - 57%

**判断理由**:
- ヘルパー関数やデコレーターは、他のテストで間接的にカバーされる
- 完全なカバレッジは必ずしも必要ない

---

## なぜ現在0%が多いのか？

### 原因: モック中心のテスト設計

現在のテストは**モックを多用**しているため：

```python
# 現在のテストスタイル
class MockApplicationType:
    @staticmethod
    def get_all_active(**kwargs):
        return [...]  # ダミーデータを返す

monkeypatch.setattr(application_type, 'ApplicationType', MockApplicationType)
```

このアプローチでは：
- ✅ **メリット**: テストが高速、DBなしで実行可能
- ❌ **デメリット**: 実際のコード（Models層、Routes層）は実行されない

---

## 改善の方向性

### 戦略1: 統合テストを追加（推奨）

実DBを使った統合テストを追加し、実際のコードパスをカバー：

```python
@pytest.mark.integration
@pytest.mark.db
def test_application_type_real_db(monkeypatch):
    """実DBから申請種類を取得"""
    # Mock DBを無効化
    monkeypatch.delenv('USE_MOCK_DB', raising=False)
    
    from app.models.application_type import ApplicationType
    app_types = ApplicationType.get_all_active()
    
    assert len(app_types) > 0
    assert 'application_type_id' in app_types[0]
```

### 戦略2: Routes層のテストを強化

実際のFlaskルートにアクセスするテストを追加：

```python
def test_application_create_route(auth_client, monkeypatch):
    """申請作成画面への実アクセス"""
    # モックを最小限にして、実際のルートハンドラーを呼ぶ
    response = auth_client.get('/application/create/1')
    assert response.status_code in [200, 302]
```

### 戦略3: 段階的な改善

**Phase 1（現在）**: モック中心の単体テスト ✅
- 高速実行
- 基本的なロジックの検証

**Phase 2（次のステップ）**: Routes層の統合テスト
- 実際のHTTPリクエスト/レスポンス
- テンプレートレンダリングの確認

**Phase 3（将来）**: 実DB統合テスト
- エンドツーエンドの動作確認
- データの整合性検証

---

## 実用的な判断基準

### ✅ 23%のカバレッジでも許容できるケース

1. **プロトタイプ段階**: 機能開発優先でOK
2. **モック中心のテスト戦略**: 意図的にモックを使っている
3. **手動テスト重視**: 画面操作での確認を重視している

### ⚠️ カバレッジを上げるべきケース

1. **本番リリース前**: 品質保証が必要
2. **リファクタリング**: 既存動作を保証したい
3. **複雑なビジネスロジック**: バグの影響が大きい

---

## 推奨アクション

### 今すぐやるべきこと

1. **現状の23%を維持**
   - 既存のテストは有効なので、そのまま活用

2. **優先度の高いモジュールから追加**
   - Routes層（画面アクセス）のテストを数件追加
   - 目標: 40-50%のカバレッジ

### 今後の改善（段階的に）

3. **統合テストの追加**
   - 実DBを使った `@pytest.mark.db` テストを追加
   - 目標: 60-70%のカバレッジ

4. **E2Eテストの充実**
   - 主要な業務シナリオを網羅
   - 目標: 80%のカバレッジ（理想）

---

## まとめ

| カバレッジ率 | 判定 | 状況 |
|------------|------|------|
| **23%** | 🟡 許容可能 | モック中心の単体テストとして妥当 |
| **40-50%** | 🟢 良好 | Routes層の統合テスト追加で達成 |
| **60-70%** | 🟢 優秀 | 実DB統合テストで達成 |
| **80%+** | 🟢 理想的 | 本番リリース前の目標 |

**現状（23%）は、モック中心のテスト戦略としては妥当です。**
優先度の高いRoutes層とModels層のテストを段階的に追加していきましょう。
