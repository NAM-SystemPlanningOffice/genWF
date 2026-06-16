# テストディレクトリ

このディレクトリには、genWFシステムの回帰テストが含まれています。

## クイックスタート

```bash
# すべてのテストを実行
pytest

# 単体テストのみ実行（高速）
pytest -m unit

# カバレッジレポート付きで実行
pytest --cov=app --cov-report=html
```

## ディレクトリ構成

- `unit/` - 単体テスト（Models, Services, Utils）
- `integration/` - 統合テスト（複数コンポーネント間の連携）
- `e2e/` - エンドツーエンドテスト（完全なユーザーフロー）
- `fixtures/` - テストデータとフィクスチャ
- `conftest.py` - 共通フィクスチャ定義

## 詳細なドキュメント

詳細な実行方法やテスト追加方法については、[TESTING.md](../docs/TESTING.md) を参照してください。

## テストマーカー

- `@pytest.mark.unit` - 単体テスト
- `@pytest.mark.integration` - 統合テスト
- `@pytest.mark.e2e` - E2Eテスト
- `@pytest.mark.auth` - 認証関連
- `@pytest.mark.application` - 申請機能
- `@pytest.mark.workflow` - ワークフロー
- `@pytest.mark.slow` - 実行時間が長いテスト
- `@pytest.mark.db` - データベースアクセスを伴うテスト
