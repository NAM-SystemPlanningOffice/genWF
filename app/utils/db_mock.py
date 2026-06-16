"""
モックデータベース（テスト用）
Oracle DBに接続できない環境でテストする場合に使用
"""
from datetime import datetime


class MockConnection:
    """モックDB接続"""

    def cursor(self):
        return MockCursor()

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class MockCursor:
    """モックカーソル"""

    def __init__(self):
        self.description = []
        self._results = []
        self.rowcount = 0

    def execute(self, sql, params=None):
        """SQLを実行（モック）"""
        sql_upper = sql.upper()

        # ユーザー情報取得
        if 'E_IMDB2_USERS' in sql_upper:
            # get_user_departments用（DISTINCT shozoku, shozoku_name）
            if 'DISTINCT' in sql_upper and 'DEPARTMENT_MAIN' in sql_upper:
                self.description = [
                    ('SHOZOKU',), ('SHOZOKU_NAME',), ('DEPARTMENT_MAIN',)
                ]
                self._results = [
                    ('1234000', 'システム企画室', '1'),
                    ('5678000', '開発部（兼務）', '0')
                ]
            # get_by_id用（基本情報）
            else:
                self.description = [
                    ('USER_ID',), ('USER_NAME',),
                    ('SHOZOKU',), ('SHOZOKU_NAME',)
                ]
                self._results = [
                    ('test_user', 'テストユーザー', '1234000', 'システム企画室')
                ]

        # 承認者取得
        elif 'E_APPROVER' in sql_upper:
            self.description = [
                ('USER_ID',), ('USER_NAME',)
            ]
            self._results = [
                ('approver1', '承認者1'),
                ('approver2', '承認者2')
            ]

        # 申請種類マスタ
        elif 'M_APPLICATION_TYPE' in sql_upper and 'SELECT' in sql_upper:
            self.description = [
                ('APPLICATION_TYPE_ID',), ('APPLICATION_TYPE_CODE',),
                ('APPLICATION_TYPE_NAME',), ('DESCRIPTION',),
                ('WORKFLOW_DEFINITION_ID',), ('IS_MULTI_RECORD',),
                ('HAS_TARGET_USER',), ('REQUIRES_JURISDICTION',),
                ('JURISDICTION_RESTRICTION',), ('ALLOWED_SHOZOKU_LIST',),
                ('SUPPORT_CREATE',), ('SUPPORT_MODIFY',), ('SUPPORT_DELETE',),
                ('RESOURCE_TABLE_NAME',), ('RESOURCE_SEARCH_QUERY',),
                ('RESOURCE_DETAIL_QUERY',), ('RESOURCE_VALIDATION_QUERY',),
                ('RESOURCE_JURISDICTION_COLUMN',), ('DISPLAY_ORDER',)
            ]
            self._results = [
                (1, 'GMAIL_GROUP', 'Gmailグループ管理',
                 'Gmailグループの新規作成・修正・削除を申請します',
                 1, 'N', 'N', 'Y', 'any', None,
                 'Y', 'Y', 'Y',
                 'T_RESOURCE_GMAIL_GROUP', None, None, None,
                 'owner_shozoku', 1),
                (2, 'DB_ACCESS', 'データベースアクセス権限申請',
                 'データベースへのアクセス権限を申請します',
                 1, 'N', 'Y', 'Y', 'any', None,
                 'Y', 'N', 'N',
                 None, None, None, None, None, 2)
            ]

        # 申請フィールドマスタ
        elif 'M_APPLICATION_FIELD' in sql_upper:
            self.description = [
                ('FIELD_ID',), ('APPLICATION_TYPE_ID',), ('FIELD_CODE',),
                ('FIELD_NAME',), ('FIELD_TYPE',),
                ('IS_REQUIRED_CREATE',), ('IS_REQUIRED_MODIFY',),
                ('IS_REQUIRED_DELETE',), ('IS_EDITABLE_MODIFY',),
                ('IS_MULTI_ROW',), ('VALIDATION_RULE_ID',),
                ('PULLDOWN_GROUP_ID',), ('RESOURCE_COLUMN_NAME',),
                ('DISPLAY_ORDER',), ('DEFAULT_VALUE',), ('PLACEHOLDER',),
                ('HELP_TEXT',), ('RULE_TYPE',), ('RULE_EXPRESSION',),
                ('MIN_VALUE',), ('MAX_VALUE',), ('MIN_LENGTH',),
                ('MAX_LENGTH',), ('VALIDATION_ERROR_MESSAGE',),
                ('PULLDOWN_GROUP_CODE',), ('PULLDOWN_IS_DYNAMIC',),
                ('PULLDOWN_DYNAMIC_QUERY',)
            ]
            self._results = [
                (1, 1, 'group_email', 'グループメールアドレス',
                 'text', 'Y', 'N', 'N', 'N', 'N', None, None, 'group_email',
                 1, None, 'example@example.com', 'グループのメールアドレスを入力',
                 None, None, None, None, None, None, None, None, None, None),
                (2, 1, 'group_name', 'グループ名',
                 'text', 'Y', 'N', 'N', 'Y', 'N', None, None, 'group_name',
                 2, None, None, 'グループの表示名を入力',
                 None, None, None, None, None, None, None, None, None, None),
                (3, 1, 'description', '説明',
                 'textarea', 'N', 'N', 'N', 'Y', 'N', None, None, 'description',
                 3, None, None, 'グループの用途や目的を記入',
                 None, None, None, None, None, None, None, None, None, None)
            ]

        # ワークフロー定義
        elif 'M_WORKFLOW_DEFINITION' in sql_upper:
            self.description = [
                ('WORKFLOW_DEFINITION_ID',), ('WORKFLOW_NAME',),
                ('WORKFLOW_CODE',), ('DESCRIPTION',),
                ('IS_ACTIVE',), ('VERSION',)
            ]
            self._results = [
                (1, '標準ワークフロー', 'STANDARD',
                 '標準的な承認フロー', 'Y', 1)
            ]

        # ワークフローノード定義
        elif 'M_WORKFLOW_NODE_DEFINITION' in sql_upper:
            self.description = [
                ('NODE_DEFINITION_ID',), ('WORKFLOW_DEFINITION_ID',),
                ('NODE_SEQ',), ('NODE_NAME',), ('NODE_TYPE',),
                ('SPECIFIC_SHOZOKU',), ('IS_REQUIRED',),
                ('SKIP_CONDITION',), ('IS_REPORT_ONLY',),
                ('APPROVER_SELECTION_REQUIRED',)
            ]
            self._results = [
                (1, 1, 1, '申請者所属長承認', 'applicant_dept',
                 None, 'Y', None, 'N', 'Y'),
                (2, 1, 2, 'システム企画室承認', 'final',
                 '1234000', 'Y', None, 'N', 'Y')
            ]

        # 申請一覧
        elif 'T_APPLICATION' in sql_upper and 'SELECT' in sql_upper:
            self.description = [
                ('APPLICATION_ID',), ('APPLICATION_TYPE_ID',),
                ('APPLICATION_TITLE',), ('APPLICATION_STATUS',),
                ('ACTION_TYPE',), ('CREATED_AT',),
                ('APPLICATION_TYPE_NAME',)
            ]
            self._results = [
                (1, 1, 'システム企画室MLの作成', 'draft',
                 'create', datetime.now(), 'Gmailグループ管理'),
                (2, 1, '開発チームMLの修正', 'submitted',
                 'modify', datetime.now(), 'Gmailグループ管理')
            ]

        # リソース検索
        elif 'T_RESOURCE_GMAIL_GROUP' in sql_upper:
            self.description = [
                ('RESOURCE_ID',), ('DISPLAY_LABEL',),
                ('GROUP_EMAIL',), ('OWNER_SHOZOKU',)
            ]
            self._results = [
                ('sys-planning@example.com',
                 'システム企画室ML (sys-planning@example.com)',
                 'sys-planning@example.com', '1234000'),
                ('dev-team@example.com',
                 '開発チームML (dev-team@example.com)',
                 'dev-team@example.com', '1235000')
            ]

        # 承認待ちタスク
        elif 'T_WORKFLOW_NODE_APPROVER' in sql_upper:
            self.description = [
                ('APPLICATION_ID',), ('APPLICATION_TITLE',),
                ('APPLICATION_TYPE_NAME',), ('ACTION_TYPE',),
                ('APPLICANT_NAME',), ('SUBMITTED_AT',),
                ('NODE_NAME',), ('DAYS_PENDING',),
                ('NODE_INSTANCE_ID',)
            ]
            self._results = [
                (1, 'システム企画室MLの作成', 'Gmailグループ管理',
                 'create', 'テストユーザー', datetime.now(),
                 '申請者所属長承認', 1, 101)
            ]

        # INSERT/UPDATE/DELETE
        elif any(x in sql_upper for x in ['INSERT', 'UPDATE', 'DELETE']):
            self.rowcount = 1
            self._results = []

        # SEQUENCE
        elif 'NEXTVAL' in sql_upper:
            self.description = [('NEXTVAL',)]
            import random
            self._results = [(random.randint(1000, 9999),)]

        # デフォルト（空の結果）
        else:
            self.description = []
            self._results = []

    def fetchone(self):
        """1行取得"""
        if self._results:
            return self._results[0]
        return None

    def fetchall(self):
        """全行取得"""
        return self._results

    def close(self):
        """カーソルを閉じる"""
        pass


def get_mock_db_connection():
    """モックDB接続を取得"""
    return MockConnection()
