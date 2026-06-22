# 管理者ガイド - 申請業務登録

管理者が申請業務やワークフローを登録・設定するためのドキュメント集です。

## 📚 ドキュメント一覧

### ワークフロー設定

- [WORKFLOW_SETUP_GUIDE.md](workflow_setup/WORKFLOW_SETUP_GUIDE.md) - **ワークフローセットアップガイド（メイン）**
- [WORKFLOW_NODE_TYPES.md](workflow_setup/WORKFLOW_NODE_TYPES.md) - ワークフローノードタイプ一覧
- [SKIP_CONDITION_EXAMPLES.md](workflow_setup/SKIP_CONDITION_EXAMPLES.md) - ノードスキップ条件の例

### 申請フィールド設定

- [APPLICATION_TYPE_FIELDS.md](application_fields/APPLICATION_TYPE_FIELDS.md) - 申請種別とフィールド設定
- [FIELD_TYPE_DATALIST.md](application_fields/FIELD_TYPE_DATALIST.md) - フィールドタイプとデータリスト
- [MULTI_RECORD_ADD_MODES.md](application_fields/MULTI_RECORD_ADD_MODES.md) - 複数レコード追加モード
- [UNIQUE_KEY_CONSTRAINT.md](application_fields/UNIQUE_KEY_CONSTRAINT.md) - ユニークキー制約の設定

### バリデーション設定

- [VALIDATION_RULES.md](validation/VALIDATION_RULES.md) - バリデーションルールの設定
- [CROSS_FIELD_VALIDATION.md](validation/CROSS_FIELD_VALIDATION.md) - 項目間バリデーションの設定

### データ一括登録

- [JSON_IMPORT_SPECIFICATION.md](data_import/JSON_IMPORT_SPECIFICATION.md) - JSON形式での一括登録仕様

## 🎯 業務登録の流れ

### 新しい申請業務を追加する

1. **ワークフロー設計**
   - [WORKFLOW_SETUP_GUIDE.md](workflow_setup/WORKFLOW_SETUP_GUIDE.md) を参照
   - 承認フローを決定
   - ノードタイプを選択 → [WORKFLOW_NODE_TYPES.md](workflow_setup/WORKFLOW_NODE_TYPES.md)

2. **申請フィールド設計**
   - [APPLICATION_TYPE_FIELDS.md](application_fields/APPLICATION_TYPE_FIELDS.md) を参照
   - フィールドタイプを選択 → [FIELD_TYPE_DATALIST.md](application_fields/FIELD_TYPE_DATALIST.md)
   - 複数レコードが必要な場合 → [MULTI_RECORD_ADD_MODES.md](application_fields/MULTI_RECORD_ADD_MODES.md)

3. **バリデーション設定**
   - 単項目バリデーション → [VALIDATION_RULES.md](validation/VALIDATION_RULES.md)
   - 項目間バリデーション → [CROSS_FIELD_VALIDATION.md](validation/CROSS_FIELD_VALIDATION.md)

4. **データ登録**
   - 手動でOracleDBに登録
   - または JSON一括登録 → [JSON_IMPORT_SPECIFICATION.md](data_import/JSON_IMPORT_SPECIFICATION.md)

### ワークフローを修正する

1. **既存ワークフローを確認** → [WORKFLOW_SETUP_GUIDE.md](workflow_setup/WORKFLOW_SETUP_GUIDE.md)
2. **スキップ条件を追加** → [SKIP_CONDITION_EXAMPLES.md](workflow_setup/SKIP_CONDITION_EXAMPLES.md)
3. **ノード追加・変更** → [WORKFLOW_NODE_TYPES.md](workflow_setup/WORKFLOW_NODE_TYPES.md)

## 💡 Tips

- **ワークフロー設定が初めて** → まず [WORKFLOW_SETUP_GUIDE.md](workflow_setup/WORKFLOW_SETUP_GUIDE.md) を読む
- **フィールドタイプがわからない** → [FIELD_TYPE_DATALIST.md](application_fields/FIELD_TYPE_DATALIST.md) で選択
- **複雑なバリデーションが必要** → [CROSS_FIELD_VALIDATION.md](validation/CROSS_FIELD_VALIDATION.md) を参照
- **一括で設定したい** → [JSON_IMPORT_SPECIFICATION.md](data_import/JSON_IMPORT_SPECIFICATION.md) を使う

## 🔗 関連ドキュメント

- 環境構築したい → [00_infrastructure/](../00_infrastructure/)
- アプリケーション構造を理解したい → [01_development/](../01_development/)
- テストを実施したい → [02_testing/](../02_testing/)
