# 承認待ちタスク一覧の設計

## 1. 現在の設計の課題

現在の`T_WORKFLOW_NODE_INSTANCE`テーブルには以下の課題があります。

### 課題1: 承認者候補が保存されていない

```sql
-- 現在の設計
T_WORKFLOW_NODE_INSTANCE
  - assigned_user_id: 単一の承認者ID（選択された人）のみ
```

**問題点**:
- 承認ノードに複数の承認者候補がいる場合、誰が承認できるかの情報がない
- 承認者候補全員に対して「承認待ち」として通知・表示できない
- 承認者が選択されるまで、誰の承認待ち一覧にも表示されない

### 課題2: 承認待ち一覧の取得SQLが複雑

複数テーブルを結合しないと、承認者のタスク一覧を取得できない。

---

## 2. 改善提案

### A. テーブル構造の追加

#### T_WORKFLOW_NODE_APPROVER (ワークフローノード承認者候補)
各ノードインスタンスの承認者候補を保持する新しいテーブル。

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| node_approver_id | NUMBER | PK | ノード承認者ID |
| node_instance_id | NUMBER | FK, NOT NULL | ノードインスタンスID |
| approver_user_id | VARCHAR2(50) | NOT NULL | 承認者候補のユーザーID |
| approver_order | NUMBER | | 承認者優先順位 |
| is_notified | CHAR(1) | NOT NULL | 通知済みフラグ（Y/N） |
| notified_at | TIMESTAMP | | 通知日時 |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |

**ユニーク制約**: (node_instance_id, approver_user_id)

**インデックス**:
- `IDX_NODE_APPROVER_USER` (approver_user_id, is_notified)
- `IDX_NODE_APPROVER_NODE` (node_instance_id)

**説明**:
- ワークフロー開始時またはノード到達時に、承認者候補を複数レコードとして登録
- 承認者全員がこのテーブルに登録され、それぞれが承認待ち一覧を取得可能
- いずれか一人が承認したら、該当ノードインスタンスの`assigned_user_id`を更新

---

### B. T_WORKFLOW_NODE_INSTANCE の修正

現在の設計に以下のカラムを追加。

| 追加カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| arrived_at | TIMESTAMP | | ノード到達日時（承認可能になった日時） |

**説明**:
- `arrived_at`: ノードが承認可能状態になった日時
  - 前のノードが承認完了した時点で設定
  - 承認待ち一覧で「到達からの経過日数」を表示するために使用

---

## 3. 承認待ち一覧取得のSQL

### 基本的な承認待ち一覧

特定ユーザーが承認すべきタスクを取得するSQL。

```sql
SELECT 
    a.application_id,
    a.application_title,
    at.application_type_name,
    a.action_type,
    a.applicant_user_id,
    au.user_name AS applicant_name,
    a.applicant_shozoku,
    a.submitted_at,
    wi.workflow_instance_id,
    ni.node_instance_id,
    ni.node_seq,
    nd.node_name,
    ni.arrived_at,
    TRUNC(SYSDATE - ni.arrived_at) AS days_pending,
    na.approver_order,
    CASE 
        WHEN ni.assigned_user_id IS NULL THEN '未割当'
        WHEN ni.assigned_user_id = :user_id THEN '自分に割当済'
        ELSE '他の承認者に割当済'
    END AS assignment_status
FROM 
    T_WORKFLOW_NODE_APPROVER na
    INNER JOIN T_WORKFLOW_NODE_INSTANCE ni 
        ON na.node_instance_id = ni.node_instance_id
    INNER JOIN T_WORKFLOW_INSTANCE wi 
        ON ni.workflow_instance_id = wi.workflow_instance_id
    INNER JOIN T_APPLICATION a 
        ON wi.application_id = a.application_id
    INNER JOIN M_APPLICATION_TYPE at 
        ON a.application_type_id = at.application_type_id
    INNER JOIN M_WORKFLOW_NODE_DEFINITION nd 
        ON ni.node_definition_id = nd.node_definition_id
    LEFT JOIN nam_user_admin.e_imdb2_users au 
        ON a.applicant_user_id = au.user_id
WHERE 
    na.approver_user_id = :user_id  -- ログインユーザー
    AND ni.node_status = 'pending'  -- 承認待ち
    AND wi.workflow_status = 'in_progress'  -- ワークフロー進行中
    AND a.application_status = 'submitted'  -- 申請済み
    AND (ni.assigned_user_id IS NULL OR ni.assigned_user_id = :user_id)  -- 未割当または自分に割当
ORDER BY 
    ni.arrived_at ASC,  -- 古い順
    a.application_id ASC
```

### フィルタ条件を追加したSQL

申請種類、所属、期間等でフィルタリング。

```sql
SELECT 
    a.application_id,
    a.application_title,
    at.application_type_name,
    a.action_type,
    a.applicant_user_id,
    au.user_name AS applicant_name,
    a.applicant_shozoku,
    s.shozoku_name AS applicant_shozoku_name,
    a.submitted_at,
    ni.node_name,
    ni.arrived_at,
    TRUNC(SYSDATE - ni.arrived_at) AS days_pending,
    CASE 
        WHEN TRUNC(SYSDATE - ni.arrived_at) >= 7 THEN '遅延'
        WHEN TRUNC(SYSDATE - ni.arrived_at) >= 3 THEN '注意'
        ELSE '正常'
    END AS urgency_level
FROM 
    T_WORKFLOW_NODE_APPROVER na
    INNER JOIN T_WORKFLOW_NODE_INSTANCE ni 
        ON na.node_instance_id = ni.node_instance_id
    INNER JOIN T_WORKFLOW_INSTANCE wi 
        ON ni.workflow_instance_id = wi.workflow_instance_id
    INNER JOIN T_APPLICATION a 
        ON wi.application_id = a.application_id
    INNER JOIN M_APPLICATION_TYPE at 
        ON a.application_type_id = at.application_type_id
    INNER JOIN M_WORKFLOW_NODE_DEFINITION nd 
        ON ni.node_definition_id = nd.node_definition_id
    LEFT JOIN nam_user_admin.e_imdb2_users au 
        ON a.applicant_user_id = au.user_id
    LEFT JOIN nam_ope.shozoku_master s  -- 所属マスタ（仮定）
        ON a.applicant_shozoku = s.shozoku_code
WHERE 
    na.approver_user_id = :user_id
    AND ni.node_status = 'pending'
    AND wi.workflow_status = 'in_progress'
    AND a.application_status = 'submitted'
    AND (ni.assigned_user_id IS NULL OR ni.assigned_user_id = :user_id)
    -- 以下、オプショナルなフィルタ条件
    AND (:application_type_id IS NULL OR a.application_type_id = :application_type_id)
    AND (:applicant_shozoku IS NULL OR a.applicant_shozoku = :applicant_shozoku)
    AND (:date_from IS NULL OR a.submitted_at >= :date_from)
    AND (:date_to IS NULL OR a.submitted_at <= :date_to)
    AND (:keyword IS NULL OR a.application_title LIKE '%' || :keyword || '%')
ORDER BY 
    CASE :sort_order
        WHEN 'urgency' THEN days_pending
        WHEN 'date' THEN EXTRACT(DAY FROM ni.arrived_at)
        ELSE a.application_id
    END DESC
```

---

## 4. 承認者候補の登録ロジック

### ワークフロー開始時

```python
def start_workflow(application_id):
    """ワークフローを開始"""
    application = get_application(application_id)
    workflow_def = get_workflow_definition(application.application_type_id)
    
    # ワークフローインスタンスを作成
    workflow_instance = create_workflow_instance(application_id, workflow_def.workflow_definition_id)
    
    # 全ノードインスタンスを作成
    for node_def in workflow_def.nodes:
        node_instance = create_node_instance(
            workflow_instance_id=workflow_instance.workflow_instance_id,
            node_definition_id=node_def.node_definition_id,
            node_seq=node_def.node_seq,
            node_status='waiting' if node_def.node_seq > 1 else 'pending'
        )
        
        # 最初のノードの場合、承認者候補を登録
        if node_def.node_seq == 1:
            register_approvers_for_node(node_instance, node_def, application)
    
    # 最初のノードを現在のノードに設定
    workflow_instance.current_node_seq = 1
    save_workflow_instance(workflow_instance)
```

### ノード到達時（承認者候補の登録）

```python
def register_approvers_for_node(node_instance, node_def, application):
    """ノードの承認者候補を登録"""
    
    # スキップ条件をチェック
    if should_skip_node(node_def, application):
        node_instance.node_status = 'skipped'
        node_instance.arrived_at = datetime.now()
        save_node_instance(node_instance)
        return
    
    # 承認者候補を取得
    approvers = get_approvers_for_node(node_def, application)
    
    if not approvers:
        raise Exception(f"承認者が見つかりません: node_seq={node_def.node_seq}")
    
    # ノードステータスを'pending'に変更
    node_instance.node_status = 'pending'
    node_instance.arrived_at = datetime.now()
    save_node_instance(node_instance)
    
    # 承認者候補を登録
    for idx, approver in enumerate(approvers):
        insert_node_approver(
            node_instance_id=node_instance.node_instance_id,
            approver_user_id=approver.user_id,
            approver_order=idx + 1
        )
    
    # 承認者候補全員に通知
    notify_approvers(node_instance, approvers, application)


def get_approvers_for_node(node_def, application):
    """ノードの承認者候補を取得"""
    
    if node_def.node_type == 'applicant_dept':
        # 申請者の所属長
        shozoku = application.applicant_shozoku
        return get_approvers_by_shozoku(shozoku)
    
    elif node_def.node_type == 'target_dept':
        # 申請対象ユーザーの所属長
        if not application.target_shozoku:
            return []
        shozoku = application.target_shozoku
        return get_approvers_by_shozoku(shozoku)
    
    elif node_def.node_type == 'jurisdiction_dept':
        # 所管所属長
        if not application.jurisdiction_shozoku:
            return []
        shozoku = application.jurisdiction_shozoku
        return get_approvers_by_shozoku(shozoku)
    
    elif node_def.node_type == 'specific_dept':
        # 特定所属（マスタで定義）
        shozoku = node_def.specific_shozoku
        return get_approvers_by_shozoku(shozoku)
    
    elif node_def.node_type == 'final':
        # 最終承認者（ノード承認者マスタから取得）
        return get_node_approvers_from_master(node_def.node_definition_id)
    
    else:
        return []


def get_approvers_by_shozoku(shozoku):
    """所属コードから承認者一覧を取得"""
    sql = """
        SELECT approver_user_id AS user_id, approver_name AS user_name
        FROM nam_ope.e_approver
        WHERE shozoku = :shozoku
        ORDER BY approver_order
    """
    return execute_query(sql, {'shozoku': shozoku})
```

---

## 5. 承認処理のロジック

### 承認実行

```python
def approve_node(node_instance_id, approver_user_id, comment):
    """ノードを承認"""
    
    node_instance = get_node_instance(node_instance_id)
    
    # 承認者候補に含まれているかチェック
    node_approver = get_node_approver(node_instance_id, approver_user_id)
    if not node_approver:
        raise Exception("承認権限がありません")
    
    # 既に承認済みかチェック
    if node_instance.node_status != 'pending':
        raise Exception("このノードは既に処理済みです")
    
    # ノードを承認済みに更新
    node_instance.node_status = 'approved'
    node_instance.assigned_user_id = approver_user_id
    node_instance.actioned_at = datetime.now()
    node_instance.action_comment = comment
    save_node_instance(node_instance)
    
    # 履歴に記録
    insert_workflow_history(
        workflow_instance_id=node_instance.workflow_instance_id,
        node_instance_id=node_instance_id,
        action_type='approve',
        action_user_id=approver_user_id,
        action_comment=comment
    )
    
    # 次のノードへ進む
    advance_to_next_node(node_instance.workflow_instance_id)
    
    # 他の承認者候補に通知（承認済みになったことを通知）
    notify_other_approvers_of_completion(node_instance, approver_user_id)


def advance_to_next_node(workflow_instance_id):
    """次のノードへ進む"""
    
    workflow_instance = get_workflow_instance(workflow_instance_id)
    application = get_application(workflow_instance.application_id)
    current_node_seq = workflow_instance.current_node_seq
    
    # 次のノードを取得
    next_node_instance = get_node_instance_by_seq(workflow_instance_id, current_node_seq + 1)
    
    if not next_node_instance:
        # 最終ノードまで完了
        workflow_instance.workflow_status = 'completed'
        workflow_instance.completed_at = datetime.now()
        
        application.application_status = 'approved'
        application.completed_at = datetime.now()
        
        save_workflow_instance(workflow_instance)
        save_application(application)
        
        # 自動設定処理を実行
        execute_auto_configuration(application)
        return
    
    # 次のノード定義を取得
    next_node_def = get_node_definition(next_node_instance.node_definition_id)
    
    # 次のノードの承認者候補を登録
    register_approvers_for_node(next_node_instance, next_node_def, application)
    
    # 現在のノードを更新
    workflow_instance.current_node_seq = current_node_seq + 1
    save_workflow_instance(workflow_instance)
```

---

## 6. 承認待ち一覧の表示例

### 画面イメージ

```
【承認待ちタスク一覧】 ログインユーザー: 山田太郎

フィルタ:
  申請種類: [すべて ▼]
  申請所属: [すべて ▼]
  緊急度: [すべて ▼]
  期間: [____/__/__ ～ ____/__/__]
  [検索]

並び替え: [到達日時(古い順) ▼]

-----------------------------------------------------------
| 申請ID | 申請種類 | 申請区分 | 申請者 | 申請日 | 現在のノード | 経過日数 | 緊急度 | 操作 |
-----------------------------------------------------------
| 00123 | Gmailグループ管理 | 新規作成 | 佐藤花子(システム企画室) | 2026-05-15 | システム企画室長承認 | 5日 | 注意 | [詳細] |
| 00124 | DBアクセス権限 | 新規作成 | 鈴木一郎(データ分析部) | 2026-05-18 | データ分析部長承認 | 2日 | 正常 | [詳細] |
| 00125 | メールエイリアス追加 | 新規作成 | 高橋次郎(システム企画室) | 2026-05-19 | システム企画室長承認 | 1日 | 正常 | [詳細] |
-----------------------------------------------------------

件数: 3件
```

### 緊急度の判定

- **遅延（赤）**: 到達から7日以上経過
- **注意（黄）**: 到達から3日以上経過
- **正常（緑）**: 到達から3日未満

---

## 7. データベース修正サマリ

### 新規テーブル

1. **T_WORKFLOW_NODE_APPROVER**
   - ノードインスタンスごとの承認者候補を保持
   - 承認待ち一覧取得の基準テーブル

### 既存テーブルの修正

1. **T_WORKFLOW_NODE_INSTANCE**
   - `arrived_at`カラムを追加（ノード到達日時）

### 新規シーケンス

```sql
CREATE SEQUENCE SEQ_NODE_APPROVER_ID START WITH 1 INCREMENT BY 1;
```

---

## 8. パフォーマンス最適化

### インデックス戦略

承認待ち一覧取得を高速化するため、以下のインデックスを作成。

```sql
-- 承認者候補テーブルの複合インデックス
CREATE INDEX IDX_NODE_APPROVER_USER_STATUS 
ON T_WORKFLOW_NODE_APPROVER(approver_user_id, node_instance_id);

-- ノードインスタンスの複合インデックス
CREATE INDEX IDX_NODE_INST_STATUS_ARRIVED 
ON T_WORKFLOW_NODE_INSTANCE(node_status, arrived_at);

-- 申請の複合インデックス
CREATE INDEX IDX_APP_STATUS_SUBMITTED 
ON T_APPLICATION(application_status, submitted_at);
```

### マテリアライズドビューの検討（オプション）

承認待ち一覧が頻繁にアクセスされる場合、マテリアライズドビューを作成。

```sql
CREATE MATERIALIZED VIEW MV_PENDING_APPROVALS
REFRESH FAST ON COMMIT
AS
SELECT 
    na.approver_user_id,
    a.application_id,
    a.application_title,
    at.application_type_name,
    a.action_type,
    a.applicant_user_id,
    a.submitted_at,
    ni.node_instance_id,
    ni.node_name,
    ni.arrived_at,
    TRUNC(SYSDATE - ni.arrived_at) AS days_pending
FROM 
    T_WORKFLOW_NODE_APPROVER na
    INNER JOIN T_WORKFLOW_NODE_INSTANCE ni ON na.node_instance_id = ni.node_instance_id
    INNER JOIN T_WORKFLOW_INSTANCE wi ON ni.workflow_instance_id = wi.workflow_instance_id
    INNER JOIN T_APPLICATION a ON wi.application_id = a.application_id
    INNER JOIN M_APPLICATION_TYPE at ON a.application_type_id = at.application_type_id
WHERE 
    ni.node_status = 'pending'
    AND wi.workflow_status = 'in_progress'
    AND a.application_status = 'submitted';
```
