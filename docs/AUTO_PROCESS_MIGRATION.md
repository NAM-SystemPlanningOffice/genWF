# 自動処理システム分離作業 - 完了報告

## 概要

ワークフローシステムから自動処理関連の機能を分離し、独立したシステムとして `../auto_process` に移動しました。

## 移動したファイル

### ドキュメント (8ファイル)
```
docs/AUTO_PROCESS_*.md → ../auto_process/docs/
```

- AUTO_PROCESS_HANDOVER.md (引き渡し資料メイン)
- AUTO_PROCESS_DB_SCHEMA.md (DBスキーマ詳細)
- AUTO_PROCESS_QUICKSTART.md (クイックスタート)
- AUTO_PROCESS_CONFIGURATION.md
- AUTO_PROCESS_EXAMPLES.md
- AUTO_PROCESS_EXAMPLES_SIMPLIFIED.md
- AUTO_PROCESS_OVERVIEW.md
- AUTO_PROCESS_SIMPLIFIED.md

### ソースコード

#### Processors (9ファイル)
```
app/processors/*.py → ../auto_process/processors/
```

- oracle_processor.py
- box_processor.py
- google_workspace_processor.py
- conditional_oracle_processor.py
- conditional_box_processor.py
- conditional_google_workspace_processor.py
- test_processor.py
- base.py
- registry.py
- __init__.py

#### Services (1ファイル)
```
app/services/auto_process_service.py → ../auto_process/services/
```

### データベース

新規作成：
- `../auto_process/database/01_create_auto_process_tables.sql`
  - M_AUTO_PROCESS_DEFINITION
  - T_AUTO_PROCESS_LOG

## ワークフローシステム側の変更

### 削除されたディレクトリ
- `app/processors/` (完全削除)

### 修正されたファイル

#### app/services/workflow_service.py
**変更内容**:
- `from app.services.auto_process_service import AutoProcessService` を削除
- `_build_auto_process_context()` メソッドを削除
- `_advance_to_next_node()` の自動処理実行ロジックを削除
- autoノードは単に `pending` にするだけに変更

**修正前**:
```python
# 自動処理実行
result = AutoProcessService.execute_node_auto_processes(
    next_node['node_instance_id'],
    context
)
if result['success']:
    # approved にして次へ
else:
    # rejected にする
```

**修正後**:
```python
# node_type='auto' の場合は外部の自動処理システムが処理を実行
# ワークフローシステムは pending にするだけ
if next_node.get('node_type') == 'auto':
    current_app.logger.info(
        f"[WorkflowService] 自動処理ノード到達: node_instance_id={next_node['node_instance_id']}"
    )
    # 外部の自動処理システムが pending ノードを検出して処理を実行
```

#### app/utils/constants.py
**追加**:
```python
NODE_STATUS_FAILED = 'failed'  # 自動処理失敗
```

### 追加されたDDL

#### database/03_add_failed_status.sql
```sql
-- T_WORKFLOW_NODE_INSTANCE に failed ステータスを追加
ALTER TABLE T_WORKFLOW_NODE_INSTANCE
DROP CONSTRAINT CHK_NODE_STATUS;

ALTER TABLE T_WORKFLOW_NODE_INSTANCE
ADD CONSTRAINT CHK_NODE_STATUS
CHECK (node_status IN ('waiting', 'pending', 'approved', 'rejected', 'returned', 'skipped', 'failed'));
```

#### database/04_drop_auto_process_tables.sql
```sql
-- 自動処理関連テーブルの削除
DROP TABLE T_AUTO_PROCESS_LOG CASCADE CONSTRAINTS;
DROP TABLE M_AUTO_PROCESS_DEFINITION CASCADE CONSTRAINTS;
DROP SEQUENCE SEQ_AUTO_PROCESS_DEFINITION;
DROP SEQUENCE SEQ_AUTO_PROCESS_LOG;
```

## 新しいアーキテクチャ

### 責任分離

| システム | 責任範囲 |
|---------|---------|
| **ワークフローシステム** | ・申請受付<br>・承認フロー管理<br>・autoノードのステータス管理（pending/approved/failed）<br>・申請データの保持 |
| **自動処理システム** | ・DBポーリング（1-5分間隔）<br>・実際の処理実行（Oracle/Box/Google等）<br>・処理結果のDB更新<br>・詳細ログ管理<br>・エラーハンドリング・リトライ |

### データフロー

```
[ワークフローシステム]
  申請 → 承認フロー → autoノード到達
  ↓
[T_WORKFLOW_NODE_INSTANCE]
  node_status = 'pending'
  ↓ (DBポーリング)
[自動処理システム]
  処理実行
  ↓
[T_WORKFLOW_NODE_INSTANCE]
  node_status = 'approved' または 'failed'
  ↓ (ワークフローシステムが検知)
[ワークフローシステム]
  次のノードへ進行 または 停止
```

### ステータス遷移

```
waiting → pending → approved (成功) → 次のノードへ
              ↓
            failed (失敗) → 停止（調査・再処理待ち）
```

## 今後の作業

### ワークフローシステム側

1. **DDL実行**
   ```sql
   @database/03_add_failed_status.sql
   @database/04_drop_auto_process_tables.sql  -- (自動処理システム側でテーブル作成後)
   ```

2. **failed ステータスの画面表示対応**
   - 承認状況画面で「システム障害発生中」を表示
   - エラーメッセージ（action_comment）を表示

3. **承認済みautoノードの進行処理** (オプション)
   - バッチ処理で定期的に `node_status = 'approved' AND node_type = 'auto'` をチェック
   - 次のノードへ自動進行
   - または、自動処理システムからのコールバックAPIを実装

### 自動処理システム側

1. **開発開始**
   - `../auto_process/docs/AUTO_PROCESS_QUICKSTART.md` に従って実装
   - 最小構成から開始し、徐々に機能追加

2. **テーブル作成**
   ```sql
   @../auto_process/database/01_create_auto_process_tables.sql
   ```

3. **本番運用準備**
   - Windows Service または systemd でのサービス化
   - 監視・アラート設定
   - ログローテーション

## 検証項目

### ワークフローシステム

- [ ] 自動処理ノードが pending になることを確認
- [ ] failed ステータスがDBに保存できることを確認
- [ ] エラーメッセージが画面に表示されることを確認（画面対応後）

### 自動処理システム

- [ ] pending ノードを正しく抽出できることを確認
- [ ] 処理実行後、approved に更新できることを確認
- [ ] エラー時、failed に更新できることを確認
- [ ] ログが正しく記録されることを確認

## ロールバック手順

万が一問題が発生した場合：

1. 自動処理システムを停止
2. ワークフローシステムの workflow_service.py を以前のバージョンに戻す
3. app/processors/ と app/services/auto_process_service.py を復元
4. DDL を元に戻す

## 完了日

2026-06-05

## 作業者

Claude Code (AI)

## 承認者

[担当者名]
