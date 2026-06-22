# スキップ条件（skip_condition）の設定例

ワークフローノード定義の`skip_condition`フィールドで、承認ノードをスキップする条件を設定できます。

## 使用可能な変数

skip_condition内で以下の変数にアクセスできます：

### 1. `application` - 申請情報

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `application.get('applicant_shozoku')` | 申請者所属 | `'1234567'` |
| `application.get('jurisdiction_shozoku')` | 所管所属 | `'1234567'` |
| `application.get('target_shozoku')` | 対象ユーザー所属 | `'7654321'` |
| `application.get('action_type')` | 申請区分 | `'create'`, `'modify'`, `'delete'` |

### 2. `resource` - リソース詳細情報

申請タイプの`resource_detail_query`で取得されるデータ。

| 例 | 説明 |
|----|------|
| `resource.get('top_folder_id')` | 最上位フォルダID |
| `resource.get('owner_shozoku')` | オーナー所属 |
| `resource.get('resource_type')` | リソースタイプ |

### 3. `fields` - 申請フィールド値

申請画面で入力されたフィールドの値。フィールドコードでアクセス。

| 例 | 説明 |
|----|------|
| `fields.get('mailaddress')` | メールアドレスフィールドの値 |
| `fields.get('groupname')` | グループ名フィールドの値 |
| `fields.get('database_name')` | データベース名フィールドの値 |

**注意**: 
- 単一レコード申請のみ対応（複数レコード申請では`detail_seq=1`の最初のレコードのみ）
- フィールドコードは`M_APPLICATION_FIELD.field_code`の値

## 設定例

### 例1: リソースの属性によるスキップ

特定のフォルダID配下のリソースの場合、法務承認をスキップ：

```python
resource.get('top_folder_id') == '0ABC9876DEF54321'
```

### 例2: 申請フィールドの値によるスキップ

メールアドレスが`@nam.co.jp`で終わる場合、外部承認をスキップ：

```python
fields.get('mailaddress', '').endswith('@nam.co.jp')
```

### 例3: 複数条件の組み合わせ

グループ名が`test-`で始まり、かつ申請者が特定所属の場合、スキップ：

```python
fields.get('groupname', '').startswith('test-') and application.get('applicant_shozoku') == '1234567'
```

### 例4: データベース名によるスキップ

データベース名が特定のパターンに一致する場合、DBA承認をスキップ：

```python
fields.get('database_name') in ['DEVDB', 'TESTDB', 'STAGINGDB']
```

### 例5: 申請区分によるスキップ

削除申請の場合、特定の承認をスキップ：

```python
application.get('action_type') == 'delete'
```

### 例6: リソースとフィールドの組み合わせ

リソースの所有者と申請で指定されたメールアドレスのドメインが一致する場合、スキップ：

```python
resource.get('owner_shozoku') == application.get('applicant_shozoku') and fields.get('mailaddress', '').endswith('@nam.co.jp')
```

### 例7: 否定条件

特定のグループ名**以外**の場合、スキップ：

```python
fields.get('groupname') not in ['production-group', 'critical-group']
```

### 例8: 部分一致

グループ名に特定の文字列が含まれる場合、スキップ：

```python
'sandbox' in fields.get('groupname', '').lower()
```

## 注意事項

### セキュリティ

- skip_conditionは`eval()`で評価されます
- 安全のため`__builtins__`は無効化されています
- 使用可能な変数は`application`, `resource`, `fields`のみです

### エラーハンドリング

- skip_conditionの評価でエラーが発生した場合、**スキップしない**（安全側に倒す）
- エラーはログに記録されます：`スキップ条件の評価エラー: ...`

### デバッグ

条件が期待通り動作しない場合、アプリケーションログを確認してください：

```powershell
Get-Content C:\inetpub\wwwroot\genWF\logs\app.log -Tail 50 | Select-String "skip"
```

### フィールドコードの確認

フィールドコードは管理画面で確認できます：

```
管理画面 > 申請タイプ管理 > [申請タイプ] > フィールド定義
```

## 管理画面での設定

`M_WORKFLOW_NODE_DEFINITION`テーブルの`skip_condition`カラムに上記の式を設定します。

例：
```sql
UPDATE M_WORKFLOW_NODE_DEFINITION
SET skip_condition = 'fields.get(''mailaddress'', '''').endswith(''@nam.co.jp'')'
WHERE node_definition_id = 123;

COMMIT;
```

**注意**: SQLでシングルクォートをエスケープする場合は`''`（2つ）にします。
