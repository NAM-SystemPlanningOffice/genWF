# ユーザー操作ログ機能

## 概要

ユーザーの利用実績を記録するために、`T_USER_LOG` テーブルにユーザーの操作ログを記録します。

## 記録されるアクション

以下の操作が自動的にログに記録されます：

| アクション | 説明 | 記録タイミング |
|----------|------|---------------|
| `save_draft` | 下書き保存 | 下書き保存ボタンクリック時 |
| `submit` | 申請提出 | 提出ボタンクリック時（承認者選択後） |
| `withdraw` | 申請取り下げ | 取り下げボタンクリック時 |
| `approve` | 承認 | 承認ボタンクリック時 |
| `return` | 差し戻し | 差し戻しボタンクリック時 |
| `reject` | 却下 | 却下ボタンクリック時 |
| `recall` | 引き戻し | 引き戻しボタンクリック時 |

## テーブル構造

```sql
CREATE TABLE T_USER_LOG (
    log_id NUMBER NOT NULL,                    -- ログID（主キー）
    user_id VARCHAR2(50) NOT NULL,            -- 操作ユーザーID
    application_id NUMBER,                     -- 申請ID
    application_type_code VARCHAR2(50),        -- 申請種類コード
    node_name VARCHAR2(200),                   -- ワークフローノード名（承認/差し戻し/却下/引き戻し時）
    action_type VARCHAR2(20) NOT NULL,        -- アクション種別
    action_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,  -- アクション実行日時
    CONSTRAINT PK_T_USER_LOG PRIMARY KEY (log_id)
);
```

## 利用例

### ユーザーごとの操作ログを取得

```sql
SELECT 
    log_id,
    user_id,
    application_id,
    application_type_code,
    node_name,
    action_type,
    action_timestamp
FROM T_USER_LOG
WHERE user_id = :user_id
ORDER BY action_timestamp DESC;
```

### 申請種類別の利用統計

```sql
SELECT 
    application_type_code,
    action_type,
    COUNT(*) as action_count
FROM T_USER_LOG
WHERE action_timestamp >= TRUNC(SYSDATE, 'MM')  -- 今月
GROUP BY application_type_code, action_type
ORDER BY application_type_code, action_type;
```

### ユーザー別の月次利用統計

```sql
SELECT 
    user_id,
    TRUNC(action_timestamp, 'MM') as month,
    COUNT(*) as total_actions,
    SUM(CASE WHEN action_type = 'submit' THEN 1 ELSE 0 END) as submit_count,
    SUM(CASE WHEN action_type = 'approve' THEN 1 ELSE 0 END) as approve_count
FROM T_USER_LOG
WHERE action_timestamp >= ADD_MONTHS(TRUNC(SYSDATE, 'MM'), -6)  -- 過去6ヶ月
GROUP BY user_id, TRUNC(action_timestamp, 'MM')
ORDER BY user_id, month DESC;
```

### 時間帯別の利用状況

```sql
SELECT 
    TO_CHAR(action_timestamp, 'HH24') as hour,
    COUNT(*) as action_count
FROM T_USER_LOG
WHERE action_timestamp >= TRUNC(SYSDATE) - 7  -- 過去7日間
GROUP BY TO_CHAR(action_timestamp, 'HH24')
ORDER BY hour;
```

## 注意事項

- ログ記録に失敗しても、ユーザー操作自体は継続されます（エラーはログ出力のみ）
- ログは削除されないため、定期的にアーカイブや削除を検討してください
- 個人情報が含まれるため、アクセス権限には注意してください
