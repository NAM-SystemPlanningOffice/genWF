# 管理画面操作の監査ログ

## 概要

管理画面での全ての作成・更新・削除操作は、T_ADMIN_AUDIT_LOGテーブルに自動的に記録されます。

## 監査ログテーブル構造

### T_ADMIN_AUDIT_LOG

| カラム名 | データ型 | 説明 |
|---------|---------|------|
| audit_log_id | NUMBER | ログID（主キー） |
| user_id | VARCHAR2(50) | 操作者のユーザーID |
| user_name | VARCHAR2(200) | 操作者の名前 |
| operation_type | VARCHAR2(20) | 操作種別（CREATE/UPDATE/DELETE/VIEW/EXPORT/OTHER） |
| table_name | VARCHAR2(100) | 対象テーブル名 |
| record_id | VARCHAR2(100) | 対象レコードID |
| operation_detail | VARCHAR2(4000) | 操作詳細（JSON形式） |
| operation_timestamp | TIMESTAMP | 操作日時 |

### インデックス

- `IDX_AUDIT_LOG_USER`: user_id, operation_timestamp DESC
- `IDX_AUDIT_LOG_TABLE`: table_name, operation_timestamp DESC
- `IDX_AUDIT_LOG_TIMESTAMP`: operation_timestamp

## 監査ログが記録される操作

### 1. 申請タイプ管理（M_APPLICATION_TYPE）
- **CREATE**: 新規申請タイプ作成時
- **UPDATE**: 申請タイプ更新時
- **記録内容**: application_type_name, application_type_code

### 2. 申請フィールド管理（M_APPLICATION_FIELD）
- **CREATE**: 新規フィールド作成時
- **UPDATE**: フィールド更新時
- **DELETE**: フィールド削除時（論理削除）
- **記録内容**: field_name, field_code, application_type_id

### 3. バリデーションルール管理（M_VALIDATION_RULE）
- **CREATE**: 新規ルール作成時
- **UPDATE**: ルール更新時
- **DELETE**: ルール削除時
- **記録内容**: rule_name, rule_code

### 4. プルダウングループ管理（M_PULLDOWN_GROUP）
- **CREATE**: 新規グループ作成時
- **UPDATE**: グループ更新時
- **DELETE**: グループ削除時
- **記録内容**: group_name, group_code

### 5. プルダウン選択肢管理（M_PULLDOWN_OPTION）
- **CREATE**: 新規選択肢作成時
- **UPDATE**: 選択肢更新時
- **DELETE**: 選択肢削除時
- **記録内容**: option_label, option_value, pulldown_group_id

### 6. ワークフロー定義管理（M_WORKFLOW_DEFINITION）
- **CREATE**: 新規ワークフロー定義作成時
- **UPDATE**: ワークフロー定義更新時
- **DELETE**: ワークフロー定義削除時
- **記録内容**: workflow_name, workflow_code

### 7. ワークフローノード定義管理（M_WORKFLOW_NODE_DEFINITION）
- **CREATE**: 新規ノード定義作成時
- **UPDATE**: ノード定義更新時
- **DELETE**: ノード定義削除時
- **記録内容**: workflow_definition_id, node_name, node_seq

### 8. 管理者ユーザー管理（M_ADMIN_USER）
- **CREATE**: 新規管理者ユーザー作成時
- **UPDATE**: 管理者ユーザー更新時
- **DELETE**: 管理者ユーザー削除時（論理削除）
- **記録内容**: user_id, user_name

### 9. ノード承認者管理（M_NODE_APPROVER）
- **CREATE**: 新規ノード承認者作成時
- **UPDATE**: ノード承認者更新時
- **DELETE**: ノード承認者削除時（論理削除）
- **記録内容**: specific_node, approver_user_id

## 監査ログの照会方法

### 最近のログを取得

```python
from app.models.admin.audit_log import AuditLog

# 最新100件を取得
logs = AuditLog.get_recent_logs(limit=100)

# 特定ユーザーの操作履歴を取得
logs = AuditLog.get_recent_logs(limit=100, user_id='user001')

# 特定テーブルの変更履歴を取得
logs = AuditLog.get_recent_logs(limit=100, table_name='M_APPLICATION_TYPE')
```

### SQLでの照会

```sql
-- 最近の管理操作を表示
SELECT 
    audit_log_id,
    user_id,
    user_name,
    operation_type,
    table_name,
    record_id,
    operation_detail,
    operation_timestamp
FROM T_ADMIN_AUDIT_LOG
ORDER BY operation_timestamp DESC
FETCH FIRST 100 ROWS ONLY;

-- 特定ユーザーの操作履歴
SELECT *
FROM T_ADMIN_AUDIT_LOG
WHERE user_id = 'user001'
ORDER BY operation_timestamp DESC;

-- 特定テーブルの変更履歴
SELECT *
FROM T_ADMIN_AUDIT_LOG
WHERE table_name = 'M_APPLICATION_TYPE'
ORDER BY operation_timestamp DESC;

-- 特定期間の操作履歴
SELECT *
FROM T_ADMIN_AUDIT_LOG
WHERE operation_timestamp >= TIMESTAMP '2026-06-01 00:00:00'
  AND operation_timestamp < TIMESTAMP '2026-07-01 00:00:00'
ORDER BY operation_timestamp DESC;

-- 削除操作のみを表示
SELECT *
FROM T_ADMIN_AUDIT_LOG
WHERE operation_type = 'DELETE'
ORDER BY operation_timestamp DESC;
```

## operation_detail の内容

operation_detailフィールドには、操作の詳細情報がJSON形式で保存されます。

### 例1: 申請タイプ作成

```json
{
    "application_type_name": "Gmailグループ申請",
    "application_type_code": "GMAIL_GROUP"
}
```

### 例2: フィールド削除

```json
{
    "field_name": "グループ名",
    "field_code": "group_name",
    "application_type_id": "1",
    "action": "論理削除"
}
```

### 例3: 管理者ユーザー更新

```json
{
    "user_id": "admin001",
    "user_name": "管理者太郎"
}
```

## セキュリティとコンプライアンス

### 監査ログの重要性

1. **変更履歴の追跡**: 誰がいつ何を変更したかを正確に記録
2. **不正操作の検知**: 異常な操作パターンの発見
3. **コンプライアンス対応**: 内部統制やセキュリティ監査への対応
4. **トラブルシューティング**: 問題発生時の原因調査

### ログ保管とアーカイブ

監査ログは長期保管が必要な場合があります。以下の運用を推奨します：

1. **定期的なアーカイブ**: 古いログを定期的に別テーブルまたは外部ストレージに移動
2. **保管期間の設定**: 法令やポリシーに基づいた保管期間の設定
3. **アクセス制限**: 監査ログへのアクセスを管理者に限定

### アーカイブ用SQL例

```sql
-- 1年以上前のログをアーカイブテーブルに移動
INSERT INTO T_ADMIN_AUDIT_LOG_ARCHIVE
SELECT * FROM T_ADMIN_AUDIT_LOG
WHERE operation_timestamp < ADD_MONTHS(SYSTIMESTAMP, -12);

-- 元テーブルから削除
DELETE FROM T_ADMIN_AUDIT_LOG
WHERE operation_timestamp < ADD_MONTHS(SYSTIMESTAMP, -12);

COMMIT;
```

## 実装の詳細

### AuditLog モデル

**ファイル**: `app/models/admin/audit_log.py`

#### log メソッド

```python
AuditLog.log(
    user_id='user001',
    user_name='ユーザー名',
    operation_type='CREATE',  # CREATE/UPDATE/DELETE/VIEW/EXPORT/OTHER
    table_name='M_APPLICATION_TYPE',
    record_id='123',
    operation_detail={  # dictまたはJSON文字列
        'key1': 'value1',
        'key2': 'value2'
    }
)
```

#### get_recent_logs メソッド

```python
logs = AuditLog.get_recent_logs(
    limit=100,              # 取得件数
    user_id='user001',      # 任意: ユーザーIDでフィルタ
    table_name='M_APPLICATION_TYPE'  # 任意: テーブル名でフィルタ
)
```

### 管理画面での使用例

```python
from app.models.admin.audit_log import AuditLog
from flask import session

# 作成時
AuditLog.log(
    user_id=session.get('user_id'),
    user_name=session.get('user_name'),
    operation_type='CREATE',
    table_name='M_APPLICATION_TYPE',
    record_id=new_id,
    operation_detail={
        'application_type_name': data['application_type_name'],
        'application_type_code': data['application_type_code']
    }
)

# 更新時
AuditLog.log(
    user_id=session.get('user_id'),
    user_name=session.get('user_name'),
    operation_type='UPDATE',
    table_name='M_APPLICATION_TYPE',
    record_id=application_type_id,
    operation_detail={
        'application_type_name': data['application_type_name'],
        'application_type_code': data['application_type_code']
    }
)

# 削除時
AuditLog.log(
    user_id=session.get('user_id'),
    user_name=session.get('user_name'),
    operation_type='DELETE',
    table_name='M_APPLICATION_TYPE',
    record_id=application_type_id,
    operation_detail={
        'application_type_name': application_type['application_type_name'],
        'application_type_code': application_type['application_type_code'],
        'action': '論理削除'
    }
)
```

## 監査ログ閲覧画面（今後の実装予定）

管理画面に監査ログの閲覧機能を追加することを推奨します：

### 必要な機能
- ログ一覧表示（最新順）
- フィルタリング（ユーザー、テーブル、操作種別、期間）
- 詳細表示（operation_detailのJSON表示）
- CSVエクスポート
- 検索機能

### 実装例URL
- `/admin/audit-logs`: 監査ログ一覧
- `/admin/audit-logs/<log_id>`: 監査ログ詳細
- `/admin/audit-logs/export`: CSVエクスポート
