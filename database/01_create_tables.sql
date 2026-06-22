-- ==========================================
-- ワークフロー申請システム - テーブル作成DDL
-- スキーマ: NAM_TASK
-- ==========================================

-- ==========================================
-- 0. シーケンスの作成
-- ==========================================

-- 申請ID用シーケンス
CREATE SEQUENCE SEQ_APPLICATION
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- 申請詳細ID用シーケンス
CREATE SEQUENCE SEQ_APPLICATION_DETAIL
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- ワークフローインスタンスID用シーケンス
CREATE SEQUENCE SEQ_WORKFLOW_INSTANCE
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- ワークフローノードインスタンスID用シーケンス
CREATE SEQUENCE SEQ_WORKFLOW_NODE_INST
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- ワークフローノード承認者ID用シーケンス
CREATE SEQUENCE SEQ_WORKFLOW_NODE_APPROVER
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- ワークフロー履歴ID用シーケンス
CREATE SEQUENCE SEQ_WORKFLOW_HISTORY
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- バリデーションルールID用シーケンス
CREATE SEQUENCE SEQ_VALIDATION_RULE
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- フィールドバリデーションID用シーケンス
CREATE SEQUENCE SEQ_FIELD_VALIDATION
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- M_NODE_APPROVER用シーケンス
CREATE SEQUENCE SEQ_M_NODE_APPROVER
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- 申請タイプID用シーケンス
CREATE SEQUENCE SEQ_APPLICATION_TYPE
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- 申請フィールドID用シーケンス
CREATE SEQUENCE SEQ_APPLICATION_FIELD
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- プルダウングループID用シーケンス
CREATE SEQUENCE SEQ_PULLDOWN_GROUP
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- プルダウン選択肢ID用シーケンス
CREATE SEQUENCE SEQ_PULLDOWN_OPTION
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- 自動処理定義ID用シーケンス
CREATE SEQUENCE SEQ_AUTO_PROCESS_DEFINITION
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- 自動処理ログID用シーケンス
CREATE SEQUENCE SEQ_AUTO_PROCESS_LOG
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- ==========================================
-- 1. 申請管理テーブル
-- ==========================================

-- 申請マスタ
CREATE TABLE T_APPLICATION (
    application_id NUMBER NOT NULL,
    application_type_id NUMBER NOT NULL,
    action_type VARCHAR2(20) NOT NULL,
    applicant_user_id VARCHAR2(50) NOT NULL,
    applicant_shozoku VARCHAR2(20) NOT NULL,
    jurisdiction_shozoku VARCHAR2(20),
    application_title VARCHAR2(200) NOT NULL,
    application_status VARCHAR2(20) NOT NULL,
    current_workflow_node_id NUMBER,
    reference_resource_id VARCHAR2(200),
    scheduled_date DATE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    submitted_at TIMESTAMP,
    completed_at TIMESTAMP,
    remarks CLOB,
    CONSTRAINT PK_T_APPLICATION PRIMARY KEY (application_id),
    CONSTRAINT CHK_APP_ACTION_TYPE CHECK (action_type IN ('create', 'modify', 'delete')),
    CONSTRAINT CHK_APP_STATUS CHECK (application_status IN ('draft', 'submitted', 'approved', 'deleted'))
);

-- インデックス
CREATE INDEX IDX_APP_STATUS ON T_APPLICATION(application_status);
CREATE INDEX IDX_APP_TYPE ON T_APPLICATION(application_type_id);
CREATE INDEX IDX_APP_ACTION ON T_APPLICATION(action_type);
CREATE INDEX IDX_APP_APPLICANT ON T_APPLICATION(applicant_user_id);
CREATE INDEX IDX_APP_JURIS ON T_APPLICATION(jurisdiction_shozoku);
CREATE INDEX IDX_APP_REF_RESOURCE ON T_APPLICATION(reference_resource_id);

-- コメント
COMMENT ON TABLE T_APPLICATION IS '申請マスタ';
COMMENT ON COLUMN T_APPLICATION.application_id IS '申請ID';
COMMENT ON COLUMN T_APPLICATION.action_type IS '申請区分（create/modify/delete）';
COMMENT ON COLUMN T_APPLICATION.jurisdiction_shozoku IS '申請対象リソースの所管所属コード';


-- 申請詳細
CREATE TABLE T_APPLICATION_DETAIL (
    detail_id NUMBER NOT NULL,
    application_id NUMBER NOT NULL,
    detail_seq NUMBER NOT NULL,
    field_id NUMBER NOT NULL,
    field_value VARCHAR2(4000),
    field_value_large CLOB,
    field_label VARCHAR2(2000),
    detail_action VARCHAR2(10) DEFAULT 'add',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT PK_T_APPLICATION_DETAIL PRIMARY KEY (detail_id),
    CONSTRAINT UK_APP_DETAIL UNIQUE (application_id, detail_seq, field_id),
    CONSTRAINT CHK_DETAIL_ACTION CHECK (detail_action IN ('add', 'modify', 'delete'))
);

-- インデックス
CREATE INDEX IDX_DETAIL_APP ON T_APPLICATION_DETAIL(application_id);

-- コメント
COMMENT ON TABLE T_APPLICATION_DETAIL IS '申請詳細（EAVモデル）';
COMMENT ON COLUMN T_APPLICATION_DETAIL.field_value IS '処理用の値（自動処理、バリデーションで使用）';
COMMENT ON COLUMN T_APPLICATION_DETAIL.field_label IS '表示用ラベル（select/datalistのoption_label。画面表示用）';
COMMENT ON COLUMN T_APPLICATION_DETAIL.detail_action IS '詳細レコードのアクション（add/modify/delete）';


-- ==========================================
-- 2. ワークフロー管理テーブル
-- ==========================================

-- ワークフローインスタンス
CREATE TABLE T_WORKFLOW_INSTANCE (
    workflow_instance_id NUMBER NOT NULL,
    application_id NUMBER NOT NULL,
    workflow_definition_id NUMBER NOT NULL,
    current_node_seq NUMBER NOT NULL,
    workflow_status VARCHAR2(20) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    CONSTRAINT PK_T_WORKFLOW_INSTANCE PRIMARY KEY (workflow_instance_id),
    CONSTRAINT CHK_WF_INST_STATUS CHECK (workflow_status IN ('in_progress', 'completed', 'rejected', 'returned', 'withdrawn'))
);

-- インデックス
CREATE INDEX IDX_WF_INST_APP ON T_WORKFLOW_INSTANCE(application_id);
CREATE INDEX IDX_WF_INST_STATUS ON T_WORKFLOW_INSTANCE(workflow_status);

-- コメント
COMMENT ON TABLE T_WORKFLOW_INSTANCE IS 'ワークフローインスタンス';


-- ワークフローノードインスタンス
CREATE TABLE T_WORKFLOW_NODE_INSTANCE (
    node_instance_id NUMBER NOT NULL,
    workflow_instance_id NUMBER NOT NULL,
    node_definition_id NUMBER NOT NULL,
    node_seq NUMBER NOT NULL,
    node_status VARCHAR2(20) NOT NULL,
    assigned_user_id VARCHAR2(50),
    arrived_at TIMESTAMP,
    assigned_at TIMESTAMP,
    actioned_at TIMESTAMP,
    action_comment VARCHAR2(2000),
    CONSTRAINT PK_T_WORKFLOW_NODE_INST PRIMARY KEY (node_instance_id),
    CONSTRAINT CHK_NODE_STATUS CHECK (node_status IN ('waiting', 'pending', 'approved', 'rejected', 'returned', 'skipped', 'failed', 'withdrawn'))
);

-- インデックス
CREATE INDEX IDX_WF_NODE_INST ON T_WORKFLOW_NODE_INSTANCE(workflow_instance_id, node_seq);
CREATE INDEX IDX_WF_NODE_ASSIGNED ON T_WORKFLOW_NODE_INSTANCE(assigned_user_id, node_status);
CREATE INDEX IDX_WF_NODE_STATUS_ARRIVED ON T_WORKFLOW_NODE_INSTANCE(node_status, arrived_at);

-- コメント
COMMENT ON TABLE T_WORKFLOW_NODE_INSTANCE IS 'ワークフローノードインスタンス';
COMMENT ON COLUMN T_WORKFLOW_NODE_INSTANCE.arrived_at IS 'ノード到達日時（承認可能になった日時）';


-- ワークフローノード承認者候補
CREATE TABLE T_WORKFLOW_NODE_APPROVER (
    node_approver_id NUMBER NOT NULL,
    node_instance_id NUMBER NOT NULL,
    approver_user_id VARCHAR2(50) NOT NULL,
    approver_group VARCHAR2(50),
    approver_order NUMBER,
    is_notified CHAR(1) DEFAULT 'N' NOT NULL,
    notified_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT PK_T_WF_NODE_APPROVER PRIMARY KEY (node_approver_id),
    CONSTRAINT UK_NODE_APPROVER UNIQUE (node_instance_id, approver_user_id),
    CONSTRAINT CHK_NODE_APPROVER_NOTIFIED CHECK (is_notified IN ('Y', 'N'))
);

-- インデックス
CREATE INDEX IDX_NODE_APPROVER_USER ON T_WORKFLOW_NODE_APPROVER(approver_user_id);
CREATE INDEX IDX_NODE_APPROVER_NODE ON T_WORKFLOW_NODE_APPROVER(node_instance_id);

-- コメント
COMMENT ON TABLE T_WORKFLOW_NODE_APPROVER IS 'ワークフローノード承認者候補';


-- ワークフロー履歴
CREATE TABLE T_WORKFLOW_HISTORY (
    history_id NUMBER NOT NULL,
    workflow_instance_id NUMBER NOT NULL,
    node_instance_id NUMBER NOT NULL,
    action_type VARCHAR2(20) NOT NULL,
    action_user_id VARCHAR2(50) NOT NULL,
    action_comment VARCHAR2(2000),
    actioned_at TIMESTAMP NOT NULL,
    CONSTRAINT PK_T_WORKFLOW_HISTORY PRIMARY KEY (history_id),
    CONSTRAINT CHK_WF_HIST_ACTION CHECK (action_type IN ('approve', 'reject', 'return', 'skip'))
);

-- インデックス
CREATE INDEX IDX_WF_HIST_INST ON T_WORKFLOW_HISTORY(workflow_instance_id);
CREATE INDEX IDX_WF_HIST_USER ON T_WORKFLOW_HISTORY(action_user_id);

-- コメント
COMMENT ON TABLE T_WORKFLOW_HISTORY IS 'ワークフロー履歴';


-- ==========================================
-- 3. マスタテーブル
-- ==========================================

-- 申請種類マスタ
CREATE TABLE M_APPLICATION_TYPE (
    application_type_id NUMBER NOT NULL,
    application_type_code VARCHAR2(50) NOT NULL,
    application_type_name VARCHAR2(200) NOT NULL,
    description VARCHAR2(1000),
    workflow_definition_id NUMBER NOT NULL,
    is_multi_record CHAR(1) DEFAULT 'N' NOT NULL,
    jurisdiction_restriction VARCHAR2(20) DEFAULT 'any',
    allowed_shozoku_list VARCHAR2(500),
    allowed_user_list VARCHAR2(2000),
    support_create CHAR(1) DEFAULT 'Y' NOT NULL,
    support_modify CHAR(1) DEFAULT 'N' NOT NULL,
    support_delete CHAR(1) DEFAULT 'N' NOT NULL,
    resource_search_query VARCHAR2(4000),
    resource_detail_query VARCHAR2(4000),
    resource_member_query CLOB,
    resource_validation_query VARCHAR2(4000),
    resource_jurisdiction_column VARCHAR2(100),
    record_add_mode VARCHAR2(20) DEFAULT 'select' NOT NULL,
    is_active CHAR(1) DEFAULT 'Y' NOT NULL,
    display_order NUMBER,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT PK_M_APPLICATION_TYPE PRIMARY KEY (application_type_id),
    CONSTRAINT UK_APP_TYPE_CODE UNIQUE (application_type_code),
    CONSTRAINT CHK_APP_TYPE_MULTI CHECK (is_multi_record IN ('Y', 'N')),
    CONSTRAINT CHK_APP_TYPE_JURIS_REST CHECK (jurisdiction_restriction IN ('any', 'specific', 'specific_user')),
    CONSTRAINT CHK_APP_TYPE_CREATE CHECK (support_create IN ('Y', 'N')),
    CONSTRAINT CHK_APP_TYPE_MODIFY CHECK (support_modify IN ('Y', 'N')),
    CONSTRAINT CHK_APP_TYPE_DELETE CHECK (support_delete IN ('Y', 'N')),
    CONSTRAINT CHK_RECORD_ADD_MODE CHECK (record_add_mode IN ('select', 'free')),
    CONSTRAINT CHK_APP_TYPE_ACTIVE CHECK (is_active IN ('Y', 'N'))
);

-- コメント
COMMENT ON TABLE M_APPLICATION_TYPE IS '申請種類マスタ';
COMMENT ON COLUMN M_APPLICATION_TYPE.jurisdiction_restriction IS '申請可能制限（any=任意/specific=特定所属のみ/specific_user=特定ユーザーのみ）';
COMMENT ON COLUMN M_APPLICATION_TYPE.allowed_shozoku_list IS '申請可能所属リスト（カンマ区切り、jurisdiction_restriction=''specific''の場合のみ有効）';
COMMENT ON COLUMN M_APPLICATION_TYPE.allowed_user_list IS '申請可能ユーザーリスト（カンマ区切り、jurisdiction_restriction=''specific_user''の場合のみ有効）';
COMMENT ON COLUMN M_APPLICATION_TYPE.record_add_mode IS '複数レコード申請時のレコード追加モード（select=候補選択/free=自由入力）';


-- 申請フィールドマスタ
CREATE TABLE M_APPLICATION_FIELD (
    field_id NUMBER NOT NULL,
    application_type_id NUMBER NOT NULL,
    field_code VARCHAR2(50) NOT NULL,
    field_name VARCHAR2(300) NOT NULL,
    field_type VARCHAR2(20) NOT NULL,
    is_required_create CHAR(1) DEFAULT 'N' NOT NULL,
    is_required_modify CHAR(1) DEFAULT 'N' NOT NULL,
    is_required_delete CHAR(1) DEFAULT 'N' NOT NULL,
    is_editable_modify CHAR(1) DEFAULT 'Y' NOT NULL,
    is_visible CHAR(1) DEFAULT 'Y' NOT NULL,
    is_key_field CHAR(1) DEFAULT 'N' NOT NULL,
    pulldown_group_id NUMBER,
    resource_column_name VARCHAR2(100),
    resource_label_column VARCHAR2(100),
    display_order NUMBER,
    default_value VARCHAR2(200),
    placeholder VARCHAR2(200),
    help_text VARCHAR2(500),
    CONSTRAINT PK_M_APPLICATION_FIELD PRIMARY KEY (field_id),
    CONSTRAINT UK_APP_FIELD UNIQUE (application_type_id, field_code),
    CONSTRAINT CHK_FIELD_TYPE CHECK (field_type IN ('text', 'number', 'date', 'select', 'datalist', 'textarea', 'checkbox')),
    CONSTRAINT CHK_FIELD_REQ_CREATE CHECK (is_required_create IN ('Y', 'N')),
    CONSTRAINT CHK_FIELD_REQ_MODIFY CHECK (is_required_modify IN ('Y', 'N')),
    CONSTRAINT CHK_FIELD_REQ_DELETE CHECK (is_required_delete IN ('Y', 'N')),
    CONSTRAINT CHK_FIELD_EDITABLE CHECK (is_editable_modify IN ('Y', 'N')),
    CONSTRAINT CHK_FIELD_MULTI_ROW CHECK (is_multi_row IN ('Y', 'N')),
    CONSTRAINT CHK_FIELD_VISIBLE CHECK (is_visible IN ('Y', 'N')),
    CONSTRAINT CHK_FIELD_KEY CHECK (is_key_field IN ('Y', 'N'))
);

-- コメント
COMMENT ON TABLE M_APPLICATION_FIELD IS '申請フィールドマスタ';
COMMENT ON COLUMN M_APPLICATION_FIELD.is_visible IS '画面に表示するか（Y/N）';
COMMENT ON COLUMN M_APPLICATION_FIELD.is_key_field IS 'キー項目か（選択時にデータ取得する）';


-- バリデーションルールマスタ（汎用的なルール定義）
CREATE TABLE M_VALIDATION_RULE (
    validation_rule_id NUMBER NOT NULL,
    rule_code VARCHAR2(50) NOT NULL,
    rule_name VARCHAR2(100) NOT NULL,
    rule_type VARCHAR2(50) NOT NULL,
    rule_parameter VARCHAR2(1000),
    error_message VARCHAR2(500) NOT NULL,
    description VARCHAR2(500),
    is_active CHAR(1) DEFAULT 'Y' NOT NULL,
    CONSTRAINT PK_M_VALIDATION_RULE PRIMARY KEY (validation_rule_id),
    CONSTRAINT UK_VALIDATION_RULE_CODE UNIQUE (rule_code),
    CONSTRAINT CHK_VALID_RULE_TYPE CHECK (rule_type IN (
        'required',
        'minlength',
        'maxlength',
        'pattern',
        'starts_with',
        'ends_with',
        'contains',
        'equals',
        'email',
        'numeric',
        'min_value',
        'max_value',
        'date_format',
        'future_date',
        'past_date',
        'exists_in_table',
        'unique_in_table',
        'custom_query',
        'cross_field'
    )),
    CONSTRAINT CHK_VALID_ACTIVE CHECK (is_active IN ('Y', 'N'))
);

-- コメント
COMMENT ON TABLE M_VALIDATION_RULE IS 'バリデーションルールマスタ（汎用的なルール定義）';
COMMENT ON COLUMN M_VALIDATION_RULE.validation_rule_id IS 'バリデーションルールID';
COMMENT ON COLUMN M_VALIDATION_RULE.rule_code IS 'ルールコード（一意）';
COMMENT ON COLUMN M_VALIDATION_RULE.rule_name IS 'ルール名';
COMMENT ON COLUMN M_VALIDATION_RULE.rule_type IS 'ルールタイプ';
COMMENT ON COLUMN M_VALIDATION_RULE.rule_parameter IS 'ルールパラメータ（JSON形式、任意）';
COMMENT ON COLUMN M_VALIDATION_RULE.error_message IS 'エラーメッセージ';
COMMENT ON COLUMN M_VALIDATION_RULE.description IS 'ルールの説明';
COMMENT ON COLUMN M_VALIDATION_RULE.is_active IS '有効フラグ（Y/N）';


-- フィールド×バリデーションルール関連テーブル
CREATE TABLE M_FIELD_VALIDATION (
    field_validation_id NUMBER NOT NULL,
    field_id NUMBER NOT NULL,
    validation_rule_id NUMBER NOT NULL,
    check_order NUMBER DEFAULT 1 NOT NULL,
    apply_on_create CHAR(1) DEFAULT 'Y' NOT NULL,
    apply_on_modify CHAR(1) DEFAULT 'Y' NOT NULL,
    is_active CHAR(1) DEFAULT 'Y' NOT NULL,
    CONSTRAINT PK_M_FIELD_VALIDATION PRIMARY KEY (field_validation_id),
    CONSTRAINT UK_FIELD_VALIDATION UNIQUE (field_id, validation_rule_id),
    CONSTRAINT CHK_FV_APPLY_CREATE CHECK (apply_on_create IN ('Y', 'N')),
    CONSTRAINT CHK_FV_APPLY_MODIFY CHECK (apply_on_modify IN ('Y', 'N')),
    CONSTRAINT CHK_FIELD_VAL_ACTIVE CHECK (is_active IN ('Y', 'N'))
);

-- コメント
COMMENT ON TABLE M_FIELD_VALIDATION IS 'フィールド×バリデーションルール関連';
COMMENT ON COLUMN M_FIELD_VALIDATION.field_validation_id IS 'フィールドバリデーションID';
COMMENT ON COLUMN M_FIELD_VALIDATION.field_id IS 'フィールドID（M_APPLICATION_FIELD）';
COMMENT ON COLUMN M_FIELD_VALIDATION.validation_rule_id IS 'バリデーションルールID';
COMMENT ON COLUMN M_FIELD_VALIDATION.check_order IS 'チェック順序（小さい方が先）';
COMMENT ON COLUMN M_FIELD_VALIDATION.apply_on_create IS '新規作成時にこのルールを適用するか（Y/N）';
COMMENT ON COLUMN M_FIELD_VALIDATION.apply_on_modify IS '編集時にこのルールを適用するか（Y/N）';
COMMENT ON COLUMN M_FIELD_VALIDATION.is_active IS '有効フラグ（Y/N）';

-- インデックス
CREATE INDEX IDX_FIELD_VALIDATION ON M_FIELD_VALIDATION(field_id, check_order);


-- プルダウングループマスタ
CREATE TABLE M_PULLDOWN_GROUP (
    pulldown_group_id NUMBER NOT NULL,
    group_code VARCHAR2(50) NOT NULL,
    group_name VARCHAR2(200) NOT NULL,
    description VARCHAR2(500),
    is_dynamic CHAR(1) DEFAULT 'N' NOT NULL,
    dynamic_query VARCHAR2(2000),
    CONSTRAINT PK_M_PULLDOWN_GROUP PRIMARY KEY (pulldown_group_id),
    CONSTRAINT UK_PULLDOWN_GROUP_CODE UNIQUE (group_code),
    CONSTRAINT CHK_PULLDOWN_DYNAMIC CHECK (is_dynamic IN ('Y', 'N'))
);

-- コメント
COMMENT ON TABLE M_PULLDOWN_GROUP IS 'プルダウングループマスタ';


-- プルダウン選択肢マスタ
CREATE TABLE M_PULLDOWN_OPTION (
    option_id NUMBER NOT NULL,
    pulldown_group_id NUMBER NOT NULL,
    option_value VARCHAR2(200) NOT NULL,
    option_label VARCHAR2(200) NOT NULL,
    display_order NUMBER,
    is_active CHAR(1) DEFAULT 'Y' NOT NULL,
    parent_option_id NUMBER,
    CONSTRAINT PK_M_PULLDOWN_OPTION PRIMARY KEY (option_id),
    CONSTRAINT CHK_PULLDOWN_OPT_ACTIVE CHECK (is_active IN ('Y', 'N'))
);

-- コメント
COMMENT ON TABLE M_PULLDOWN_OPTION IS 'プルダウン選択肢マスタ';


-- ==========================================
-- 4. ワークフロー定義テーブル
-- ==========================================

-- ワークフロー定義マスタ
CREATE TABLE M_WORKFLOW_DEFINITION (
    workflow_definition_id NUMBER NOT NULL,
    workflow_name VARCHAR2(200) NOT NULL,
    workflow_code VARCHAR2(50) NOT NULL,
    description VARCHAR2(1000),
    is_active CHAR(1) DEFAULT 'Y' NOT NULL,
    version NUMBER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT PK_M_WORKFLOW_DEF PRIMARY KEY (workflow_definition_id),
    CONSTRAINT UK_WORKFLOW_CODE UNIQUE (workflow_code),
    CONSTRAINT CHK_WORKFLOW_ACTIVE CHECK (is_active IN ('Y', 'N'))
);

-- コメント
COMMENT ON TABLE M_WORKFLOW_DEFINITION IS 'ワークフロー定義マスタ';


-- ワークフローノード定義マスタ
CREATE TABLE M_WORKFLOW_NODE_DEFINITION (
    node_definition_id NUMBER NOT NULL,
    workflow_definition_id NUMBER NOT NULL,
    node_seq NUMBER NOT NULL,
    node_name VARCHAR2(200) NOT NULL,
    node_type VARCHAR2(50) NOT NULL,
    specific_value VARCHAR2(50),
    skip_condition VARCHAR2(500),
    is_report_only CHAR(1) DEFAULT 'N' NOT NULL,
    approver_selection_required CHAR(1) DEFAULT 'N' NOT NULL,
    CONSTRAINT PK_M_WORKFLOW_NODE_DEF PRIMARY KEY (node_definition_id),
    CONSTRAINT UK_WORKFLOW_NODE UNIQUE (workflow_definition_id, node_seq),
    CONSTRAINT CHK_NODE_TYPE CHECK (node_type IN ('applicant_dept', 'jurisdiction_dept', 'specific_node', 'specific_dept', 'resource_dept', 'multiple_dept', 'report', 'auto')),
    CONSTRAINT CHK_NODE_REPORT CHECK (is_report_only IN ('Y', 'N')),
    CONSTRAINT CHK_NODE_APPROVER_SEL CHECK (approver_selection_required IN ('Y', 'N'))
);

-- コメント
COMMENT ON TABLE M_WORKFLOW_NODE_DEFINITION IS 'ワークフローノード定義マスタ';
COMMENT ON COLUMN M_WORKFLOW_NODE_DEFINITION.node_type IS 'ノードタイプ: applicant_dept, jurisdiction_dept, specific_node, specific_dept, resource_dept, multiple_dept, report, auto';
COMMENT ON COLUMN M_WORKFLOW_NODE_DEFINITION.specific_value IS '特定値（node_typeに応じた値: specific_node→識別子, specific_dept→部署コード, resource_dept→テーブル名, auto→process_code）';


-- ノード承認者マスタ
CREATE TABLE M_NODE_APPROVER (
    node_approver_id NUMBER NOT NULL,
    specific_node VARCHAR2(50) NOT NULL,
    approver_user_id VARCHAR2(50) NOT NULL,
    approver_order NUMBER,
    is_active CHAR(1) DEFAULT 'Y' NOT NULL,
    CONSTRAINT PK_M_NODE_APPROVER PRIMARY KEY (node_approver_id),
    CONSTRAINT CHK_NODE_APPROVER_ACTIVE CHECK (is_active IN ('Y', 'N'))
);

-- コメント
COMMENT ON TABLE M_NODE_APPROVER IS 'ノード承認者マスタ';


-- ==========================================
-- 5. リソーステーブル（サンプル）
-- ==========================================

-- Gmailグループリソース（サンプル）
CREATE TABLE T_RESOURCE_GMAIL_GROUP (
    resource_id VARCHAR2(200) NOT NULL,
    group_name VARCHAR2(200) NOT NULL,
    group_email VARCHAR2(200) NOT NULL,
    description VARCHAR2(1000),
    owner_shozoku VARCHAR2(20),
    member_count NUMBER,
    created_date DATE,
    last_updated TIMESTAMP NOT NULL,
    is_active CHAR(1) DEFAULT 'Y' NOT NULL,
    sync_source VARCHAR2(50),
    CONSTRAINT PK_T_RESOURCE_GMAIL_GROUP PRIMARY KEY (resource_id),
    CONSTRAINT UK_GMAIL_GROUP_EMAIL UNIQUE (group_email),
    CONSTRAINT CHK_GMAIL_GROUP_ACTIVE CHECK (is_active IN ('Y', 'N'))
);

-- インデックス
CREATE INDEX IDX_GMAIL_GROUP_EMAIL ON T_RESOURCE_GMAIL_GROUP(group_email);
CREATE INDEX IDX_GMAIL_GROUP_OWNER ON T_RESOURCE_GMAIL_GROUP(owner_shozoku);

-- コメント
COMMENT ON TABLE T_RESOURCE_GMAIL_GROUP IS 'Gmailグループリソース';


-- リソース同期ログ
CREATE TABLE T_RESOURCE_SYNC_LOG (
    sync_log_id NUMBER NOT NULL,
    resource_table_name VARCHAR2(100) NOT NULL,
    sync_start_time TIMESTAMP NOT NULL,
    sync_end_time TIMESTAMP,
    sync_status VARCHAR2(20) NOT NULL,
    records_processed NUMBER,
    records_inserted NUMBER,
    records_updated NUMBER,
    records_deleted NUMBER,
    error_message CLOB,
    executed_by VARCHAR2(50),
    CONSTRAINT PK_T_RESOURCE_SYNC_LOG PRIMARY KEY (sync_log_id),
    CONSTRAINT CHK_SYNC_STATUS CHECK (sync_status IN ('success', 'failed', 'partial'))
);

-- インデックス
CREATE INDEX IDX_SYNC_LOG_TABLE ON T_RESOURCE_SYNC_LOG(resource_table_name, sync_start_time);

-- コメント
COMMENT ON TABLE T_RESOURCE_SYNC_LOG IS 'リソース同期ログ';


-- ==========================================
-- 6. 自動処理テーブル
-- ==========================================

-- 自動処理定義マスタ
CREATE TABLE M_AUTO_PROCESS_DEFINITION (
    auto_process_id NUMBER NOT NULL,
    process_code VARCHAR2(50) NOT NULL,
    process_name VARCHAR2(100) NOT NULL,
    process_type VARCHAR2(20) NOT NULL,
    handler_class VARCHAR2(100) NOT NULL,
    description VARCHAR2(500),
    config_json CLOB,
    is_active CHAR(1) DEFAULT 'Y' NOT NULL,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    updated_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT PK_AUTO_PROCESS_DEF PRIMARY KEY (auto_process_id),
    CONSTRAINT UK_AUTO_PROCESS_CODE UNIQUE (process_code),
    CONSTRAINT CHK_AUTO_PROC_TYPE CHECK (process_type IN ('box', 'google', 'oracle', 'custom')),
    CONSTRAINT CHK_AUTO_PROC_ACTIVE CHECK (is_active IN ('Y', 'N'))
);

COMMENT ON TABLE M_AUTO_PROCESS_DEFINITION IS '自動処理定義マスタ';
COMMENT ON COLUMN M_AUTO_PROCESS_DEFINITION.auto_process_id IS '自動処理ID';
COMMENT ON COLUMN M_AUTO_PROCESS_DEFINITION.process_code IS '処理コード（例: ORACLE_INSERT_USER, BOX_ADD_COLLAB）';
COMMENT ON COLUMN M_AUTO_PROCESS_DEFINITION.process_name IS '処理名（表示用）';
COMMENT ON COLUMN M_AUTO_PROCESS_DEFINITION.process_type IS '処理種別: box, google, oracle, custom';
COMMENT ON COLUMN M_AUTO_PROCESS_DEFINITION.handler_class IS 'Pythonクラス名（例: app.processors.oracle_processor.OracleProcessor）';
COMMENT ON COLUMN M_AUTO_PROCESS_DEFINITION.description IS '処理説明';
COMMENT ON COLUMN M_AUTO_PROCESS_DEFINITION.config_json IS 'プロセッサ設定（JSON形式）: 認証情報、action_typeごとの処理定義、パラメータマッピング（{{applicant.user_id}}, {{application_data.1001}}等）、制御情報（retry_count, timeout_seconds, on_error）。例: {"auth_type": "env", "retry_count": 3, "timeout_seconds": 300, "on_error": "fail", "create": {...}, "modify": {...}, "delete": {...}, "mappings": {"user_id": "{{application_data.1001}}"}}';
COMMENT ON COLUMN M_AUTO_PROCESS_DEFINITION.is_active IS '有効フラグ';

-- 自動処理実行ログ
CREATE TABLE T_AUTO_PROCESS_LOG (
    log_id NUMBER NOT NULL,
    node_instance_id NUMBER NOT NULL,
    auto_process_id NUMBER NOT NULL,
    execution_time TIMESTAMP DEFAULT SYSTIMESTAMP,
    status VARCHAR2(20) NOT NULL,
    request_json CLOB,
    response_json CLOB,
    error_message VARCHAR2(2000),
    retry_attempt NUMBER DEFAULT 0,
    completed_at TIMESTAMP,
    CONSTRAINT PK_AUTO_PROCESS_LOG PRIMARY KEY (log_id),
    CONSTRAINT FK_AUTO_LOG_NODE_INST FOREIGN KEY (node_instance_id) REFERENCES T_WORKFLOW_NODE_INSTANCE(node_instance_id),
    CONSTRAINT FK_AUTO_LOG_AUTO_PROC FOREIGN KEY (auto_process_id) REFERENCES M_AUTO_PROCESS_DEFINITION(auto_process_id),
    CONSTRAINT CHK_AUTO_LOG_STATUS CHECK (status IN ('pending', 'running', 'success', 'failed'))
);

COMMENT ON TABLE T_AUTO_PROCESS_LOG IS '自動処理実行ログ';
COMMENT ON COLUMN T_AUTO_PROCESS_LOG.log_id IS 'ログID';
COMMENT ON COLUMN T_AUTO_PROCESS_LOG.node_instance_id IS 'ノードインスタンスID';
COMMENT ON COLUMN T_AUTO_PROCESS_LOG.auto_process_id IS '自動処理ID';
COMMENT ON COLUMN T_AUTO_PROCESS_LOG.execution_time IS '実行開始時刻';
COMMENT ON COLUMN T_AUTO_PROCESS_LOG.status IS 'ステータス: pending(待機中), running(実行中), success(成功), failed(失敗)';
COMMENT ON COLUMN T_AUTO_PROCESS_LOG.request_json IS '実行時パラメータ（JSON形式）';
COMMENT ON COLUMN T_AUTO_PROCESS_LOG.response_json IS '実行結果（JSON形式）';
COMMENT ON COLUMN T_AUTO_PROCESS_LOG.error_message IS 'エラーメッセージ';
COMMENT ON COLUMN T_AUTO_PROCESS_LOG.retry_attempt IS 'リトライ試行回数';
COMMENT ON COLUMN T_AUTO_PROCESS_LOG.completed_at IS '完了時刻';

CREATE INDEX IDX_AUTO_LOG_NODE ON T_AUTO_PROCESS_LOG(node_instance_id);
CREATE INDEX IDX_AUTO_LOG_STATUS ON T_AUTO_PROCESS_LOG(status);
CREATE INDEX IDX_AUTO_LOG_PROC ON T_AUTO_PROCESS_LOG(auto_process_id);


-- ==========================================
-- 7. ユーザー操作ログテーブル
-- ==========================================

-- ユーザー操作ログ
CREATE TABLE T_USER_LOG (
    log_id NUMBER NOT NULL,
    user_id VARCHAR2(50) NOT NULL,
    application_id NUMBER,
    application_type_code VARCHAR2(50),
    node_name VARCHAR2(200),
    action_type VARCHAR2(20) NOT NULL,
    action_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT PK_T_USER_LOG PRIMARY KEY (log_id)
);

-- インデックス
CREATE INDEX IDX_USER_LOG_USER ON T_USER_LOG(user_id, action_timestamp);
CREATE INDEX IDX_USER_LOG_APP ON T_USER_LOG(application_id);
CREATE INDEX IDX_USER_LOG_TYPE ON T_USER_LOG(application_type_code, action_timestamp);

-- コメント
COMMENT ON TABLE T_USER_LOG IS 'ユーザー操作ログ';
COMMENT ON COLUMN T_USER_LOG.log_id IS 'ログID';
COMMENT ON COLUMN T_USER_LOG.user_id IS '操作ユーザーID';
COMMENT ON COLUMN T_USER_LOG.application_id IS '申請ID';
COMMENT ON COLUMN T_USER_LOG.application_type_code IS '申請種類コード';
COMMENT ON COLUMN T_USER_LOG.node_name IS 'ワークフローノード名';
COMMENT ON COLUMN T_USER_LOG.action_type IS 'アクション種別（save_draft/submit/withdraw/approve/return/reject/recall）';
COMMENT ON COLUMN T_USER_LOG.action_timestamp IS 'アクション実行日時';

-- ユーザー操作ログID用シーケンス
CREATE SEQUENCE SEQ_USER_LOG
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- 管理操作監査ログID用シーケンス
CREATE SEQUENCE SEQ_ADMIN_AUDIT_LOG
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;


-- ==========================================
-- 8. 管理画面操作ログテーブル
-- ==========================================

-- 管理操作監査ログ
CREATE TABLE T_ADMIN_AUDIT_LOG (
    audit_log_id NUMBER NOT NULL,
    user_id VARCHAR2(50) NOT NULL,
    user_name VARCHAR2(200),
    operation_type VARCHAR2(20) NOT NULL,
    table_name VARCHAR2(100),
    record_id VARCHAR2(100),
    operation_detail VARCHAR2(4000),
    operation_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT PK_ADMIN_AUDIT_LOG PRIMARY KEY (audit_log_id),
    CONSTRAINT CHK_AUDIT_OP_TYPE CHECK (operation_type IN ('CREATE', 'UPDATE', 'DELETE', 'VIEW', 'EXPORT', 'OTHER'))
);

-- インデックス
CREATE INDEX IDX_AUDIT_LOG_USER ON T_ADMIN_AUDIT_LOG(user_id, operation_timestamp DESC);
CREATE INDEX IDX_AUDIT_LOG_TABLE ON T_ADMIN_AUDIT_LOG(table_name, operation_timestamp DESC);
CREATE INDEX IDX_AUDIT_LOG_TIMESTAMP ON T_ADMIN_AUDIT_LOG(operation_timestamp);

-- コメント
COMMENT ON TABLE T_ADMIN_AUDIT_LOG IS '管理画面操作ログ';
COMMENT ON COLUMN T_ADMIN_AUDIT_LOG.audit_log_id IS 'ログID';
COMMENT ON COLUMN T_ADMIN_AUDIT_LOG.user_id IS '操作者のユーザーID';
COMMENT ON COLUMN T_ADMIN_AUDIT_LOG.user_name IS '操作者の名前';
COMMENT ON COLUMN T_ADMIN_AUDIT_LOG.operation_type IS '操作種別（CREATE/UPDATE/DELETE等）';
COMMENT ON COLUMN T_ADMIN_AUDIT_LOG.table_name IS '対象テーブル名';
COMMENT ON COLUMN T_ADMIN_AUDIT_LOG.record_id IS '対象レコードID';
COMMENT ON COLUMN T_ADMIN_AUDIT_LOG.operation_detail IS '操作詳細（JSON形式）';
COMMENT ON COLUMN T_ADMIN_AUDIT_LOG.operation_timestamp IS '操作日時';


-- ==========================================
-- 9. シーケンス
-- ==========================================

CREATE SEQUENCE SEQ_DETAIL_ID START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE SEQ_WORKFLOW_INSTANCE_ID START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE SEQ_NODE_INSTANCE_ID START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE SEQ_NODE_APPROVER_ID START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE SEQ_HISTORY_ID START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE SEQ_SYNC_LOG_ID START WITH 1 INCREMENT BY 1 NOCACHE;
