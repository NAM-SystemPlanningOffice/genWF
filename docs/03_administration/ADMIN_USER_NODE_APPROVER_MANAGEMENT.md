# 管理者ユーザーとノード承認者の管理画面

## 概要

M_ADMIN_USERテーブルとM_NODE_APPROVERテーブルのメンテナンス画面を提供します。

## 実装内容

### 1. データベース変更

#### M_ADMIN_USER テーブルへの is_active カラム追加

- **ファイル**: `database/alter_admin_user_add_is_active.sql`
- **内容**:
  - `is_active` カラムを追加（CHAR(1), デフォルト: 'Y'）
  - CHECK制約を追加（'Y' または 'N'）
  - 既存データは全て有効（'Y'）として設定

**実行方法**:
```sql
sqlplus NAM_TASK/password@database @database/alter_admin_user_add_is_active.sql
```

### 2. モデルクラスの更新・追加

#### AdminUser モデルの更新
- **ファイル**: `app/models/admin_user.py`
- **変更点**:
  - `get_all()`: is_activeカラムを含める、`include_inactive`パラメータを追加
  - `get_by_id()`: 新規追加（IDで管理者を取得）
  - `create()`: 新規作成メソッド（is_active対応）
  - `update()`: 更新メソッド（is_active対応）
  - `is_admin()`: 有効な管理者のみをチェック（is_active = 'Y'）
  - `add()`: 後方互換性のため残す

#### NodeApprover モデルの追加
- **ファイル**: `app/models/admin/node_approver.py`
- **メソッド**:
  - `get_all(include_inactive=False)`: 全ノード承認者を取得
  - `get_by_id(node_approver_id)`: IDでノード承認者を取得
  - `get_by_specific_node(specific_node, include_inactive=False)`: 特定ノードの承認者を取得
  - `create(data)`: ノード承認者を追加
  - `update(node_approver_id, data)`: ノード承認者を更新
  - `delete(node_approver_id)`: ノード承認者を削除（論理削除）

### 3. ルーティングの追加

**ファイル**: `app/routes/admin.py`

#### 管理者ユーザー管理
- `GET /admin/admin-users`: 管理者ユーザー一覧
- `GET /admin/admin-users/new`: 新規作成画面
- `GET /admin/admin-users/<user_id>/edit`: 編集画面
- `POST /admin/admin-users/save`: 保存処理
- `POST /admin/admin-users/<user_id>/delete`: 削除処理（論理削除）

#### ノード承認者管理
- `GET /admin/node-approvers`: ノード承認者一覧
- `GET /admin/node-approvers/new`: 新規作成画面
- `GET /admin/node-approvers/<node_approver_id>/edit`: 編集画面
- `POST /admin/node-approvers/save`: 保存処理
- `POST /admin/node-approvers/<node_approver_id>/delete`: 削除処理（論理削除）

### 4. テンプレートファイル

#### 管理者ユーザー管理画面
- `app/templates/admin/admin_user_list.html`: 一覧画面
- `app/templates/admin/admin_user_edit.html`: 編集/新規作成画面

#### ノード承認者管理画面
- `app/templates/admin/node_approver_list.html`: 一覧画面
- `app/templates/admin/node_approver_edit.html`: 編集/新規作成画面

#### 管理画面トップ
- `app/templates/admin/index.html`: 新しいメニューを追加

## 使用方法

### 1. データベース更新

既存のM_ADMIN_USERテーブルにis_activeカラムを追加：

```bash
# 本番環境
sqlplus NAM_TASK/password@com-db @database/alter_admin_user_add_is_active.sql

# 開発環境
sqlplus NAM_TASK/password@com-dbdv @database/alter_admin_user_add_is_active.sql
```

### 2. 管理画面へのアクセス

1. 管理者権限でログイン
2. 管理画面トップ（`/admin`）にアクセス
3. 以下のメニューが追加されています：
   - **管理者ユーザー管理**: 管理者ユーザーの作成・編集・削除
   - **ノード承認者管理**: 特定ノードの承認者の管理

### 3. 管理者ユーザーの管理

#### 新規作成
1. 「新規作成」ボタンをクリック
2. 以下の情報を入力：
   - ユーザーID（必須）
   - ユーザー名（任意）
   - 有効フラグ（チェックボックス）
3. 「保存」ボタンをクリック

#### 編集
1. 一覧画面で「編集」ボタンをクリック
2. 情報を変更（ユーザーIDは変更不可）
3. 「保存」ボタンをクリック

#### 削除
1. 一覧画面で「削除」ボタンをクリック
2. 確認ダイアログで「OK」をクリック
3. 論理削除（is_active = 'N'）が実行されます

### 4. ノード承認者の管理

#### 新規作成
1. 「新規作成」ボタンをクリック
2. 以下の情報を入力：
   - 特定ノード識別子（必須）
     - 例: `keiei_planning`（経営企画部長）、`legal_compliance`（法務コンプライアンス部長）
   - 承認者ユーザーID（必須）
   - 承認順序（任意、数値）
   - 有効フラグ（チェックボックス）
3. 「保存」ボタンをクリック

#### 編集
1. 一覧画面で「編集」ボタンをクリック
2. 情報を変更
3. 「保存」ボタンをクリック

#### 削除
1. 一覧画面で「削除」ボタンをクリック
2. 確認ダイアログで「OK」をクリック
3. 論理削除（is_active = 'N'）が実行されます

## 監査ログ

全ての管理操作（作成・更新・削除）は、T_ADMIN_AUDIT_LOGテーブルに自動的に記録されます。

### 記録される情報
- 操作者のユーザーID・ユーザー名
- 操作種別（CREATE/UPDATE/DELETE）
- 対象テーブル名
- 対象レコードID
- 操作詳細（JSON形式）
- 操作日時

詳細は [AUDIT_LOG.md](./AUDIT_LOG.md) を参照してください。

## 注意事項

1. **削除は論理削除**:
   - 両方のテーブルとも物理削除ではなく、is_active = 'N' に設定する論理削除です
   - データは残るため、必要に応じて再有効化が可能です

2. **管理者権限が必要**:
   - これらの画面にアクセスするには、M_ADMIN_USERに登録されている必要があります
   - 自分自身を無効化すると管理画面にアクセスできなくなるので注意してください

3. **監査ログの記録**:
   - 全ての作成・更新・削除操作は監査ログに記録されます
   - 誰がいつ何を変更したかを追跡できます

4. **ユーザーIDの変更不可**:
   - 管理者ユーザーのユーザーIDは編集画面では変更できません
   - 必要な場合は新規作成して古いレコードを無効化してください

## 特定ノード識別子の例

ワークフローノード定義で使用される特定ノード識別子の例：

- `keiei_planning`: 経営企画部長
- `legal_compliance`: 法務コンプライアンス部長
- `hr_dept`: 人事部長
- `it_dept`: IT部門長

これらの識別子は、M_WORKFLOW_NODE_DEFINITIONテーブルの`specific_value`カラムで使用されます（node_type = 'specific_node' の場合）。
