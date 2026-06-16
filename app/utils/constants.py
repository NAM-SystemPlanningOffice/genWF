"""
定数定義
"""

# 申請ステータス
APPLICATION_STATUS_DRAFT = 'draft'
APPLICATION_STATUS_SUBMITTED = 'submitted'
APPLICATION_STATUS_APPROVED = 'approved'

# 申請区分
ACTION_TYPE_CREATE = 'create'
ACTION_TYPE_MODIFY = 'modify'
ACTION_TYPE_DELETE = 'delete'

# ワークフローステータス
WORKFLOW_STATUS_IN_PROGRESS = 'in_progress'
WORKFLOW_STATUS_COMPLETED = 'completed'
WORKFLOW_STATUS_REJECTED = 'rejected'
WORKFLOW_STATUS_RETURNED = 'returned'  # 差し戻し
WORKFLOW_STATUS_WITHDRAWN = 'withdrawn'  # 取り下げ

# ノードステータス
NODE_STATUS_WAITING = 'waiting'
NODE_STATUS_PENDING = 'pending'
NODE_STATUS_APPROVED = 'approved'
NODE_STATUS_REJECTED = 'rejected'
NODE_STATUS_RETURNED = 'returned'
NODE_STATUS_SKIPPED = 'skipped'
NODE_STATUS_FAILED = 'failed'  # 自動処理失敗
NODE_STATUS_WITHDRAWN = 'withdrawn'  # 取り下げ

# ノード種別
NODE_TYPE_APPLICANT_DEPT = 'applicant_dept'           # 申請者所属長承認
NODE_TYPE_JURISDICTION_DEPT = 'jurisdiction_dept'     # 所管所属長承認（リソースがユーザーの場合は対象ユーザー所属長承認）
NODE_TYPE_SPECIFIC_NODE = 'specific_node'             # 特定ノード（承認者はM_NODE_APPROVERで管理）
NODE_TYPE_SPECIFIC_DEPT = 'specific_dept'             # 特定部署承認（e_approverから承認者を取得）
NODE_TYPE_RESOURCE_DEPT = 'resource_dept'             # リソース所管承認（resource_idとshozokuから承認者を取得）
NODE_TYPE_MULTIPLE_DEPT = 'multiple_dept'             # 複数所属長承認（複数レコード申請で変更される所属の所属長）
NODE_TYPE_FINAL = 'final'                             # 最終承認
NODE_TYPE_REPORT = 'report'                           # 報告

# アクション種別
WORKFLOW_ACTION_APPROVE = 'approve'
WORKFLOW_ACTION_REJECT = 'reject'
WORKFLOW_ACTION_RETURN = 'return'
WORKFLOW_ACTION_SKIP = 'skip'

# フィールドタイプ
FIELD_TYPE_TEXT = 'text'
FIELD_TYPE_NUMBER = 'number'
FIELD_TYPE_DATE = 'date'
FIELD_TYPE_SELECT = 'select'
FIELD_TYPE_DATALIST = 'datalist'  # プルダウン候補表示+自由入力可能
FIELD_TYPE_TEXTAREA = 'textarea'
FIELD_TYPE_CHECKBOX = 'checkbox'

# バリデーションルールタイプ
VALIDATION_RULE_CROSS_FIELD = 'cross_field'

# 所管所属制限
JURISDICTION_RESTRICTION_ANY = 'any'
JURISDICTION_RESTRICTION_JURISDICTION_ONLY = 'jurisdiction_only'
JURISDICTION_RESTRICTION_SPECIFIC = 'specific'
