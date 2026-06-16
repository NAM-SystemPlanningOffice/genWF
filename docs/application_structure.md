# Flaskアプリケーション構成案

## 1. ディレクトリ構成

```
genWF/
│
├── app/                          # アプリケーション本体
│   ├── __init__.py              # Flaskアプリケーションファクトリ
│   ├── config.py                # 設定ファイル
│   │
│   ├── models/                  # データモデル（DB操作）
│   │   ├── __init__.py
│   │   ├── application.py       # 申請関連モデル
│   │   ├── workflow.py          # ワークフロー関連モデル
│   │   ├── master.py            # マスタ関連モデル
│   │   ├── resource.py          # リソーステーブル関連モデル
│   │   └── user.py              # ユーザー情報モデル
│   │
│   ├── services/                # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── application_service.py    # 申請処理サービス
│   │   ├── workflow_service.py       # ワークフロー処理サービス
│   │   ├── approval_service.py       # 承認処理サービス
│   │   ├── validation_service.py     # バリデーションサービス
│   │   ├── resource_service.py       # リソース検索サービス
│   │   └── notification_service.py   # 通知サービス
│   │
│   ├── routes/                  # ルーティング（コントローラー）
│   │   ├── __init__.py
│   │   ├── auth.py              # 認証関連
│   │   ├── application.py       # 申請画面
│   │   ├── approval.py          # 承認画面
│   │   ├── admin.py             # 管理画面
│   │   └── api.py               # API（Ajax用）
│   │
│   ├── templates/               # HTMLテンプレート（Jinja2）
│   │   ├── base.html            # ベーステンプレート
│   │   ├── layout/              # レイアウト部品
│   │   │   ├── header.html
│   │   │   ├── footer.html
│   │   │   ├── sidebar.html
│   │   │   └── breadcrumb.html
│   │   │
│   │   ├── auth/                # 認証画面
│   │   │   ├── login.html
│   │   │   └── logout.html
│   │   │
│   │   ├── application/         # 申請画面
│   │   │   ├── index.html       # 申請種類選択
│   │   │   ├── create.html      # 新規申請作成
│   │   │   ├── modify.html      # 修正申請
│   │   │   ├── delete.html      # 削除申請
│   │   │   ├── search_resource.html  # リソース検索
│   │   │   ├── confirm.html     # 申請確認
│   │   │   ├── list.html        # 申請一覧
│   │   │   └── detail.html      # 申請詳細
│   │   │
│   │   ├── approval/            # 承認画面
│   │   │   ├── task_list.html   # 承認待ちタスク一覧
│   │   │   ├── task_detail.html # タスク詳細・承認
│   │   │   ├── approved_list.html  # 承認済み一覧
│   │   │   └── history.html     # 承認履歴
│   │   │
│   │   ├── admin/               # 管理画面
│   │   │   ├── dashboard.html   # ダッシュボード
│   │   │   ├── application_type.html     # 申請種類管理
│   │   │   ├── field_definition.html     # フィールド定義管理
│   │   │   ├── workflow_definition.html  # ワークフロー定義管理
│   │   │   ├── validation_rule.html      # バリデーションルール管理
│   │   │   ├── pulldown_option.html      # プルダウン選択肢管理
│   │   │   └── resource_sync.html        # リソース同期管理
│   │   │
│   │   ├── components/          # 再利用可能コンポーネント
│   │   │   ├── form_field.html  # フォームフィールド
│   │   │   ├── table.html       # テーブル
│   │   │   ├── pagination.html  # ページネーション
│   │   │   └── modal.html       # モーダルダイアログ
│   │   │
│   │   └── errors/              # エラー画面
│   │       ├── 400.html
│   │       ├── 403.html
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   ├── static/                  # 静的ファイル
│   │   ├── css/
│   │   │   ├── style.css        # メインスタイル
│   │   │   └── admin.css        # 管理画面用スタイル
│   │   ├── js/
│   │   │   ├── main.js          # メインJavaScript
│   │   │   ├── application.js   # 申請画面用JS
│   │   │   ├── approval.js      # 承認画面用JS
│   │   │   └── admin.js         # 管理画面用JS
│   │   └── images/
│   │
│   └── utils/                   # ユーティリティ
│       ├── __init__.py
│       ├── db.py                # DB接続管理
│       ├── validators.py        # バリデーター
│       ├── decorators.py        # デコレーター（認証等）
│       ├── helpers.py           # ヘルパー関数
│       └── constants.py         # 定数定義
│
├── migrations/                  # DBマイグレーション（必要に応じて）
│
├── tests/                       # テストコード
│   ├── __init__.py
│   ├── test_application.py
│   ├── test_workflow.py
│   └── test_approval.py
│
├── scripts/                     # バッチスクリプト
│   ├── sync_resources.py        # リソース同期バッチ
│   └── send_notifications.py    # 通知送信バッチ
│
├── logs/                        # ログファイル
│
├── docs/                        # ドキュメント（既存）
│
├── .env                         # 環境変数（Gitにコミットしない）
├── .env.example                 # 環境変数のサンプル
├── requirements.txt             # Python依存パッケージ
├── config.ini                   # 設定ファイル
├── wsgi.py                      # WSGI エントリーポイント
└── run.py                       # 開発サーバー起動スクリプト
```

---

## 2. 主要Pythonファイルの構成と関数

### 2.1 app/__init__.py（アプリケーションファクトリ）

```python
"""
Flaskアプリケーションファクトリ
"""
from flask import Flask
from app.utils.db import init_db
from app.routes import auth, application, approval, admin, api


def create_app(config_name='default'):
    """
    Flaskアプリケーションを作成
    
    Args:
        config_name: 設定名（development/production/testing）
    
    Returns:
        Flask: Flaskアプリケーションインスタンス
    """
    app = Flask(__name__)
    
    # 設定読み込み
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')
    
    # データベース初期化
    init_db(app)
    
    # Blueprintを登録
    app.register_blueprint(auth.bp)
    app.register_blueprint(application.bp)
    app.register_blueprint(approval.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)
    
    # エラーハンドラー登録
    register_error_handlers(app)
    
    # テンプレートフィルター登録
    register_template_filters(app)
    
    return app


def register_error_handlers(app):
    """エラーハンドラーを登録"""
    @app.errorhandler(400)
    def bad_request(error):
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html'), 500


def register_template_filters(app):
    """テンプレートフィルターを登録"""
    from app.utils.helpers import format_date, format_status
    
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_status'] = format_status
```

---

### 2.2 app/config.py（設定ファイル）

```python
"""
アプリケーション設定
"""
import os
from datetime import timedelta


class Config:
    """基本設定"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # セッション設定
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Oracle DB接続設定
    ORACLE_DSN = os.environ.get('ORACLE_DSN')
    ORACLE_USER = os.environ.get('ORACLE_USER')
    ORACLE_PASSWORD = os.environ.get('ORACLE_PASSWORD')
    ORACLE_ENCODING = 'UTF-8'
    
    # アプリケーション設定
    ITEMS_PER_PAGE = 20  # ページネーション
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
    
    # ログ設定
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'


class DevelopmentConfig(Config):
    """開発環境設定"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """本番環境設定"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    """テスト環境設定"""
    TESTING = True
    DEBUG = True
```

---

### 2.3 app/models/application.py（申請モデル）

```python
"""
申請関連のデータモデル
"""
from app.utils.db import get_db_connection
from datetime import datetime


class Application:
    """申請モデル"""
    
    @staticmethod
    def create(data):
        """
        新規申請を作成
        
        Args:
            data: 申請データ（辞書）
        
        Returns:
            int: 作成された申請ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 申請IDを採番
            cursor.execute("SELECT SEQ_APPLICATION_ID.NEXTVAL FROM DUAL")
            application_id = cursor.fetchone()[0]
            
            # T_APPLICATIONにINSERT
            sql = """
                INSERT INTO T_APPLICATION (
                    application_id, application_type_id, action_type,
                    applicant_user_id, applicant_shozoku,
                    target_user_id, target_shozoku, jurisdiction_shozoku,
                    application_title, application_status,
                    created_at, updated_at, remarks
                ) VALUES (
                    :application_id, :application_type_id, :action_type,
                    :applicant_user_id, :applicant_shozoku,
                    :target_user_id, :target_shozoku, :jurisdiction_shozoku,
                    :application_title, :application_status,
                    :created_at, :updated_at, :remarks
                )
            """
            
            cursor.execute(sql, {
                'application_id': application_id,
                'application_type_id': data['application_type_id'],
                'action_type': data['action_type'],
                'applicant_user_id': data['applicant_user_id'],
                'applicant_shozoku': data['applicant_shozoku'],
                'target_user_id': data.get('target_user_id'),
                'target_shozoku': data.get('target_shozoku'),
                'jurisdiction_shozoku': data.get('jurisdiction_shozoku'),
                'application_title': data['application_title'],
                'application_status': 'draft',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'remarks': data.get('remarks')
            })
            
            conn.commit()
            return application_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    
    @staticmethod
    def get_by_id(application_id):
        """
        申請IDから申請情報を取得
        
        Args:
            application_id: 申請ID
        
        Returns:
            dict: 申請情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = """
            SELECT 
                a.*,
                at.application_type_name,
                at.application_type_code,
                au.user_name AS applicant_name
            FROM T_APPLICATION a
            INNER JOIN M_APPLICATION_TYPE at ON a.application_type_id = at.application_type_id
            LEFT JOIN nam_user_admin.e_imdb2_users au ON a.applicant_user_id = au.user_id
            WHERE a.application_id = :application_id
        """
        
        cursor.execute(sql, {'application_id': application_id})
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            return dict(zip([col[0].lower() for col in cursor.description], row))
        return None
    
    
    @staticmethod
    def update(application_id, data):
        """
        申請を更新
        
        Args:
            application_id: 申請ID
            data: 更新データ
        
        Returns:
            bool: 成功したかどうか
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
                UPDATE T_APPLICATION
                SET 
                    application_title = :application_title,
                    updated_at = :updated_at,
                    remarks = :remarks
                WHERE application_id = :application_id
            """
            
            cursor.execute(sql, {
                'application_id': application_id,
                'application_title': data['application_title'],
                'updated_at': datetime.now(),
                'remarks': data.get('remarks')
            })
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    
    @staticmethod
    def submit(application_id):
        """
        申請を提出
        
        Args:
            application_id: 申請ID
        
        Returns:
            bool: 成功したかどうか
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
                UPDATE T_APPLICATION
                SET 
                    application_status = 'submitted',
                    submitted_at = :submitted_at,
                    updated_at = :updated_at
                WHERE application_id = :application_id
                  AND application_status = 'draft'
            """
            
            cursor.execute(sql, {
                'application_id': application_id,
                'submitted_at': datetime.now(),
                'updated_at': datetime.now()
            })
            
            if cursor.rowcount == 0:
                raise Exception("申請の提出に失敗しました")
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    
    @staticmethod
    def get_list(user_id, filters=None, page=1, per_page=20):
        """
        申請一覧を取得
        
        Args:
            user_id: ユーザーID
            filters: フィルタ条件（辞書）
            page: ページ番号
            per_page: 1ページあたりの件数
        
        Returns:
            tuple: (申請リスト, 総件数)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # WHERE句を構築
        where_conditions = ["a.applicant_user_id = :user_id"]
        params = {'user_id': user_id}
        
        if filters:
            if filters.get('status'):
                where_conditions.append("a.application_status = :status")
                params['status'] = filters['status']
            
            if filters.get('application_type_id'):
                where_conditions.append("a.application_type_id = :application_type_id")
                params['application_type_id'] = filters['application_type_id']
        
        where_clause = " AND ".join(where_conditions)
        
        # 総件数取得
        count_sql = f"""
            SELECT COUNT(*)
            FROM T_APPLICATION a
            WHERE {where_clause}
        """
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]
        
        # データ取得
        offset = (page - 1) * per_page
        params['offset'] = offset
        params['limit'] = per_page
        
        data_sql = f"""
            SELECT 
                a.*,
                at.application_type_name
            FROM T_APPLICATION a
            INNER JOIN M_APPLICATION_TYPE at ON a.application_type_id = at.application_type_id
            WHERE {where_clause}
            ORDER BY a.created_at DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """
        
        cursor.execute(data_sql, params)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        applications = []
        for row in rows:
            applications.append(dict(zip([col[0].lower() for col in cursor.description], row)))
        
        return applications, total_count


class ApplicationDetail:
    """申請詳細モデル"""
    
    @staticmethod
    def create_batch(application_id, details):
        """
        申請詳細を一括作成
        
        Args:
            application_id: 申請ID
            details: 詳細データのリスト
        
        Returns:
            bool: 成功したかどうか
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
                INSERT INTO T_APPLICATION_DETAIL (
                    detail_id, application_id, detail_seq, field_id,
                    field_value, field_value_large,
                    created_at, updated_at
                ) VALUES (
                    SEQ_DETAIL_ID.NEXTVAL, :application_id, :detail_seq, :field_id,
                    :field_value, :field_value_large,
                    :created_at, :updated_at
                )
            """
            
            for detail in details:
                cursor.execute(sql, {
                    'application_id': application_id,
                    'detail_seq': detail['detail_seq'],
                    'field_id': detail['field_id'],
                    'field_value': detail.get('field_value'),
                    'field_value_large': detail.get('field_value_large'),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    
    @staticmethod
    def get_by_application_id(application_id):
        """
        申請IDから詳細データを取得
        
        Args:
            application_id: 申請ID
        
        Returns:
            list: 詳細データのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = """
            SELECT 
                d.*,
                f.field_code,
                f.field_name,
                f.field_type
            FROM T_APPLICATION_DETAIL d
            INNER JOIN M_APPLICATION_FIELD f ON d.field_id = f.field_id
            WHERE d.application_id = :application_id
            ORDER BY d.detail_seq, f.display_order
        """
        
        cursor.execute(sql, {'application_id': application_id})
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        details = []
        for row in rows:
            details.append(dict(zip([col[0].lower() for col in cursor.description], row)))
        
        return details
```

---

### 2.4 app/models/workflow.py（ワークフローモデル）

```python
"""
ワークフロー関連のデータモデル
"""
from app.utils.db import get_db_connection
from datetime import datetime


class WorkflowInstance:
    """ワークフローインスタンスモデル"""
    
    @staticmethod
    def create(application_id, workflow_definition_id):
        """
        ワークフローインスタンスを作成
        
        Args:
            application_id: 申請ID
            workflow_definition_id: ワークフロー定義ID
        
        Returns:
            int: ワークフローインスタンスID
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT SEQ_WORKFLOW_INSTANCE_ID.NEXTVAL FROM DUAL")
            workflow_instance_id = cursor.fetchone()[0]
            
            sql = """
                INSERT INTO T_WORKFLOW_INSTANCE (
                    workflow_instance_id, application_id, workflow_definition_id,
                    current_node_seq, workflow_status, started_at
                ) VALUES (
                    :workflow_instance_id, :application_id, :workflow_definition_id,
                    1, 'in_progress', :started_at
                )
            """
            
            cursor.execute(sql, {
                'workflow_instance_id': workflow_instance_id,
                'application_id': application_id,
                'workflow_definition_id': workflow_definition_id,
                'started_at': datetime.now()
            })
            
            conn.commit()
            return workflow_instance_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    
    @staticmethod
    def get_by_application_id(application_id):
        """
        申請IDからワークフローインスタンスを取得
        
        Args:
            application_id: 申請ID
        
        Returns:
            dict: ワークフローインスタンス情報
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = """
            SELECT *
            FROM T_WORKFLOW_INSTANCE
            WHERE application_id = :application_id
        """
        
        cursor.execute(sql, {'application_id': application_id})
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            return dict(zip([col[0].lower() for col in cursor.description], row))
        return None


class WorkflowNodeInstance:
    """ワークフローノードインスタンスモデル"""
    
    @staticmethod
    def create(workflow_instance_id, node_definition_id, node_seq, node_status='waiting'):
        """
        ノードインスタンスを作成
        
        Args:
            workflow_instance_id: ワークフローインスタンスID
            node_definition_id: ノード定義ID
            node_seq: ノード順序番号
            node_status: ノードステータス
        
        Returns:
            int: ノードインスタンスID
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT SEQ_NODE_INSTANCE_ID.NEXTVAL FROM DUAL")
            node_instance_id = cursor.fetchone()[0]
            
            sql = """
                INSERT INTO T_WORKFLOW_NODE_INSTANCE (
                    node_instance_id, workflow_instance_id, node_definition_id,
                    node_seq, node_status
                ) VALUES (
                    :node_instance_id, :workflow_instance_id, :node_definition_id,
                    :node_seq, :node_status
                )
            """
            
            cursor.execute(sql, {
                'node_instance_id': node_instance_id,
                'workflow_instance_id': workflow_instance_id,
                'node_definition_id': node_definition_id,
                'node_seq': node_seq,
                'node_status': node_status
            })
            
            conn.commit()
            return node_instance_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    
    @staticmethod
    def update_status(node_instance_id, status, user_id=None, comment=None):
        """
        ノードステータスを更新
        
        Args:
            node_instance_id: ノードインスタンスID
            status: 新しいステータス
            user_id: 処理したユーザーID
            comment: コメント
        
        Returns:
            bool: 成功したかどうか
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
                UPDATE T_WORKFLOW_NODE_INSTANCE
                SET 
                    node_status = :node_status,
                    assigned_user_id = :assigned_user_id,
                    actioned_at = :actioned_at,
                    action_comment = :action_comment
                WHERE node_instance_id = :node_instance_id
            """
            
            cursor.execute(sql, {
                'node_instance_id': node_instance_id,
                'node_status': status,
                'assigned_user_id': user_id,
                'actioned_at': datetime.now() if user_id else None,
                'action_comment': comment
            })
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    
    @staticmethod
    def get_pending_tasks(user_id, filters=None, page=1, per_page=20):
        """
        ユーザーの承認待ちタスク一覧を取得
        
        Args:
            user_id: ユーザーID
            filters: フィルタ条件
            page: ページ番号
            per_page: 1ページあたりの件数
        
        Returns:
            tuple: (タスクリスト, 総件数)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        where_conditions = [
            "na.approver_user_id = :user_id",
            "ni.node_status = 'pending'",
            "wi.workflow_status = 'in_progress'",
            "a.application_status = 'submitted'",
            "(ni.assigned_user_id IS NULL OR ni.assigned_user_id = :user_id)"
        ]
        
        params = {'user_id': user_id}
        
        if filters:
            if filters.get('application_type_id'):
                where_conditions.append("a.application_type_id = :application_type_id")
                params['application_type_id'] = filters['application_type_id']
        
        where_clause = " AND ".join(where_conditions)
        
        # 総件数
        count_sql = f"""
            SELECT COUNT(DISTINCT ni.node_instance_id)
            FROM T_WORKFLOW_NODE_APPROVER na
            INNER JOIN T_WORKFLOW_NODE_INSTANCE ni ON na.node_instance_id = ni.node_instance_id
            INNER JOIN T_WORKFLOW_INSTANCE wi ON ni.workflow_instance_id = wi.workflow_instance_id
            INNER JOIN T_APPLICATION a ON wi.application_id = a.application_id
            WHERE {where_clause}
        """
        
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]
        
        # データ取得
        offset = (page - 1) * per_page
        params['offset'] = offset
        params['limit'] = per_page
        
        data_sql = f"""
            SELECT 
                a.application_id,
                a.application_title,
                at.application_type_name,
                a.action_type,
                a.applicant_user_id,
                au.user_name AS applicant_name,
                a.submitted_at,
                ni.node_instance_id,
                nd.node_name,
                ni.arrived_at,
                TRUNC(SYSDATE - ni.arrived_at) AS days_pending
            FROM T_WORKFLOW_NODE_APPROVER na
            INNER JOIN T_WORKFLOW_NODE_INSTANCE ni ON na.node_instance_id = ni.node_instance_id
            INNER JOIN T_WORKFLOW_INSTANCE wi ON ni.workflow_instance_id = wi.workflow_instance_id
            INNER JOIN T_APPLICATION a ON wi.application_id = a.application_id
            INNER JOIN M_APPLICATION_TYPE at ON a.application_type_id = at.application_type_id
            INNER JOIN M_WORKFLOW_NODE_DEFINITION nd ON ni.node_definition_id = nd.node_definition_id
            LEFT JOIN nam_user_admin.e_imdb2_users au ON a.applicant_user_id = au.user_id
            WHERE {where_clause}
            ORDER BY ni.arrived_at ASC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """
        
        cursor.execute(data_sql, params)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append(dict(zip([col[0].lower() for col in cursor.description], row)))
        
        return tasks, total_count


class WorkflowNodeApprover:
    """ワークフローノード承認者モデル"""
    
    @staticmethod
    def create_batch(node_instance_id, approvers):
        """
        承認者候補を一括登録
        
        Args:
            node_instance_id: ノードインスタンスID
            approvers: 承認者リスト
        
        Returns:
            bool: 成功したかどうか
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
                INSERT INTO T_WORKFLOW_NODE_APPROVER (
                    node_approver_id, node_instance_id, approver_user_id,
                    approver_order, is_notified, created_at
                ) VALUES (
                    SEQ_NODE_APPROVER_ID.NEXTVAL, :node_instance_id, :approver_user_id,
                    :approver_order, 'N', :created_at
                )
            """
            
            for idx, approver in enumerate(approvers):
                cursor.execute(sql, {
                    'node_instance_id': node_instance_id,
                    'approver_user_id': approver['user_id'],
                    'approver_order': idx + 1,
                    'created_at': datetime.now()
                })
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
```

---

## 3. 次のファイル

続きを次のメッセージで作成します:
- services（ビジネスロジック）
- routes（コントローラー）
- HTMLテンプレート構成の詳細
