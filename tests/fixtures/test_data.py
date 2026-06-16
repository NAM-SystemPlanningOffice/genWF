"""
テストデータのフィクスチャ
"""


class TestData:
    """テストデータの定義"""

    # ユーザーデータ
    USERS = {
        'applicant': {
            'user_id': 'test_applicant',
            'user_name': '申請者テスト',
            'shozoku': '1234000',
            'shozoku_name': 'テスト部署'
        },
        'approver1': {
            'user_id': 'test_approver1',
            'user_name': '承認者1',
            'shozoku': '1234000',
            'shozoku_name': 'テスト部署'
        },
        'approver2': {
            'user_id': 'test_approver2',
            'user_name': '承認者2（システム企画室）',
            'shozoku': '1230000',
            'shozoku_name': 'システム企画室'
        },
        'admin': {
            'user_id': 'test_admin',
            'user_name': '管理者',
            'shozoku': '1230000',
            'shozoku_name': 'システム企画室'
        }
    }

    # 申請種類データ
    APPLICATION_TYPES = [
        {
            'application_type_id': 1,
            'application_type_name': 'Gmailグループ作成',
            'application_type_description': 'Gmailグループの新規作成申請',
            'support_create': 'Y',
            'support_modify': 'Y',
            'support_delete': 'Y',
            'is_multi_record': 'N',
            'workflow_definition_id': 1,
            'is_published': 'Y',
            'restrict_shozoku': None,
            'restrict_user_id': None
        },
        {
            'application_type_id': 2,
            'application_type_name': 'ユーザー権限変更',
            'application_type_description': 'ユーザーのシステム権限変更申請',
            'support_create': 'Y',
            'support_modify': 'Y',
            'support_delete': 'N',
            'is_multi_record': 'Y',
            'workflow_definition_id': 2,
            'is_published': 'Y',
            'restrict_shozoku': None,
            'restrict_user_id': None
        },
        {
            'application_type_id': 3,
            'application_type_name': 'データベース権限申請',
            'application_type_description': 'データベースアクセス権限の申請',
            'support_create': 'Y',
            'support_modify': 'N',
            'support_delete': 'Y',
            'is_multi_record': 'N',
            'workflow_definition_id': 3,
            'is_published': 'Y',
            'restrict_shozoku': '1230000',  # システム企画室のみ
            'restrict_user_id': None
        }
    ]

    # 申請フィールドデータ
    APPLICATION_FIELDS = {
        1: [  # Gmailグループ作成
            {
                'field_id': 1,
                'application_type_id': 1,
                'field_name': 'group_email',
                'field_label': 'グループメールアドレス',
                'field_type': 'text',
                'is_required_create': 'Y',
                'is_required_modify': 'Y',
                'display_order': 1,
                'pulldown_group_id': None,
                'help_text': '例: group-name@example.com'
            },
            {
                'field_id': 2,
                'application_type_id': 1,
                'field_name': 'group_description',
                'field_label': 'グループ説明',
                'field_type': 'textarea',
                'is_required_create': 'Y',
                'is_required_modify': 'N',
                'display_order': 2,
                'pulldown_group_id': None,
                'help_text': 'グループの用途を記載'
            },
            {
                'field_id': 3,
                'application_type_id': 1,
                'field_name': 'owner_user_id',
                'field_label': 'オーナー',
                'field_type': 'select',
                'is_required_create': 'Y',
                'is_required_modify': 'Y',
                'display_order': 3,
                'pulldown_group_id': 1,
                'help_text': 'グループの管理者'
            }
        ],
        2: [  # ユーザー権限変更
            {
                'field_id': 4,
                'application_type_id': 2,
                'field_name': 'target_user_id',
                'field_label': '対象ユーザーID',
                'field_type': 'datalist',
                'is_required_create': 'Y',
                'is_required_modify': 'Y',
                'display_order': 1,
                'pulldown_group_id': 2,
                'help_text': 'ユーザーIDを入力または選択'
            },
            {
                'field_id': 5,
                'application_type_id': 2,
                'field_name': 'permission_level',
                'field_label': '権限レベル',
                'field_type': 'select',
                'is_required_create': 'Y',
                'is_required_modify': 'Y',
                'display_order': 2,
                'pulldown_group_id': 3,
                'help_text': '付与する権限を選択'
            }
        ]
    }

    # プルダウングループデータ
    PULLDOWN_GROUPS = [
        {
            'pulldown_group_id': 1,
            'group_name': 'ユーザー一覧',
            'is_dynamic': 'Y',
            'dynamic_sql': 'SELECT user_id AS value, user_name AS label FROM e_imdb2_users WHERE shozoku = :applicant_shozoku ORDER BY user_id'
        },
        {
            'pulldown_group_id': 2,
            'group_name': '全ユーザー一覧',
            'is_dynamic': 'Y',
            'dynamic_sql': 'SELECT user_id AS value, user_name AS label FROM e_imdb2_users ORDER BY user_id'
        },
        {
            'pulldown_group_id': 3,
            'group_name': '権限レベル',
            'is_dynamic': 'N',
            'dynamic_sql': None
        }
    ]

    # プルダウンオプションデータ
    PULLDOWN_OPTIONS = {
        3: [  # 権限レベル
            {
                'option_id': 1,
                'pulldown_group_id': 3,
                'option_value': 'read',
                'option_label': '参照権限',
                'display_order': 1
            },
            {
                'option_id': 2,
                'pulldown_group_id': 3,
                'option_value': 'write',
                'option_label': '編集権限',
                'display_order': 2
            },
            {
                'option_id': 3,
                'pulldown_group_id': 3,
                'option_value': 'admin',
                'option_label': '管理者権限',
                'display_order': 3
            }
        ]
    }

    # ワークフロー定義データ
    WORKFLOW_DEFINITIONS = [
        {
            'workflow_definition_id': 1,
            'workflow_name': '標準承認フロー',
            'workflow_description': '所属長 → システム企画室'
        },
        {
            'workflow_definition_id': 2,
            'workflow_name': '複雑な承認フロー',
            'workflow_description': '所属長 → 所管部署 → システム企画室'
        },
        {
            'workflow_definition_id': 3,
            'workflow_name': '部長承認フロー',
            'workflow_description': '所属長 → システム企画室 → 開発部長'
        }
    ]

    # ワークフローノード定義データ
    WORKFLOW_NODES = {
        1: [  # 標準承認フロー
            {
                'node_definition_id': 1,
                'workflow_definition_id': 1,
                'node_seq': 1,
                'node_name': '所属長承認',
                'node_type': 'approval',
                'approver_shozoku_type': 'applicant',
                'approver_user_ids': None,
                'is_optional': 'N'
            },
            {
                'node_definition_id': 2,
                'workflow_definition_id': 1,
                'node_seq': 2,
                'node_name': 'システム企画室承認',
                'node_type': 'approval',
                'approver_shozoku_type': 'fixed',
                'fixed_shozoku': '1230000',
                'approver_user_ids': None,
                'is_optional': 'N'
            }
        ],
        2: [  # 複雑な承認フロー
            {
                'node_definition_id': 3,
                'workflow_definition_id': 2,
                'node_seq': 1,
                'node_name': '所属長承認',
                'node_type': 'approval',
                'approver_shozoku_type': 'applicant',
                'is_optional': 'N'
            },
            {
                'node_definition_id': 4,
                'workflow_definition_id': 2,
                'node_seq': 2,
                'node_name': '所管部署承認',
                'node_type': 'approval',
                'approver_shozoku_type': 'jurisdiction',
                'is_optional': 'Y'  # 申請者所属と同じ場合はスキップ
            },
            {
                'node_definition_id': 5,
                'workflow_definition_id': 2,
                'node_seq': 3,
                'node_name': 'システム企画室承認',
                'node_type': 'approval',
                'approver_shozoku_type': 'fixed',
                'fixed_shozoku': '1230000',
                'is_optional': 'N'
            }
        ]
    }

    # 申請データサンプル
    APPLICATIONS = [
        {
            'application_id': 1,
            'application_type_id': 1,
            'action_type': 'create',
            'applicant_user_id': 'test_applicant',
            'applicant_shozoku': '1234000',
            'jurisdiction_shozoku': '1234000',
            'application_title': 'テストグループ作成',
            'remarks': 'テスト用のGmailグループ',
            'status': 'pending',
            'created_at': '2026-06-15 10:00:00',
            'updated_at': '2026-06-15 10:00:00'
        }
    ]

    # 申請詳細データサンプル
    APPLICATION_DETAILS = {
        1: [
            {
                'detail_id': 1,
                'application_id': 1,
                'detail_seq': 1,
                'field_id': 1,
                'field_value': 'test-group@example.com'
            },
            {
                'detail_id': 2,
                'application_id': 1,
                'detail_seq': 1,
                'field_id': 2,
                'field_value': 'テスト用グループです'
            },
            {
                'detail_id': 3,
                'application_id': 1,
                'detail_seq': 1,
                'field_id': 3,
                'field_value': 'test_applicant'
            }
        ]
    }

    # バリデーションルールデータ
    VALIDATION_RULES = [
        {
            'validation_rule_id': 1,
            'rule_name': 'メールアドレス形式',
            'rule_type': 'regex',
            'rule_value': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'error_message': '正しいメールアドレス形式で入力してください'
        },
        {
            'validation_rule_id': 2,
            'rule_name': '最大文字数100',
            'rule_type': 'max_length',
            'rule_value': '100',
            'error_message': '100文字以内で入力してください'
        },
        {
            'validation_rule_id': 3,
            'rule_name': '7桁の数字',
            'rule_type': 'regex',
            'rule_value': r'^\d{7}$',
            'error_message': '7桁の数字で入力してください'
        }
    ]

    # フィールドバリデーション関連付け
    FIELD_VALIDATIONS = {
        1: [1],  # group_email → メールアドレス形式
        2: [2],  # group_description → 最大文字数100
        4: [3],  # target_user_id → 7桁の数字
    }


def get_user(user_type='applicant'):
    """ユーザーデータ取得"""
    return TestData.USERS.get(user_type)


def get_application_type(app_type_id=1):
    """申請種類データ取得"""
    return next((at for at in TestData.APPLICATION_TYPES if at['application_type_id'] == app_type_id), None)


def get_application_fields(app_type_id=1):
    """申請フィールドデータ取得"""
    return TestData.APPLICATION_FIELDS.get(app_type_id, [])


def get_workflow_definition(workflow_def_id=1):
    """ワークフロー定義取得"""
    return next((wd for wd in TestData.WORKFLOW_DEFINITIONS if wd['workflow_definition_id'] == workflow_def_id), None)


def get_workflow_nodes(workflow_def_id=1):
    """ワークフローノード取得"""
    return TestData.WORKFLOW_NODES.get(workflow_def_id, [])
