"""
管理画面操作ログモデル
"""
import json
from datetime import datetime
from app.utils.db import get_db_connection, dict_factory


class AuditLog:
    """管理画面操作ログモデル"""

    @staticmethod
    def log(user_id, user_name, operation_type, table_name=None, record_id=None, operation_detail=None):
        """
        管理操作のログを記録

        Args:
            user_id: 操作者のユーザーID
            user_name: 操作者の名前
            operation_type: 操作種別（CREATE/UPDATE/DELETE等）
            table_name: 対象テーブル名
            record_id: 対象レコードID
            operation_detail: 操作詳細（dict形式で渡すとJSON化される）

        Returns:
            int: ログID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # operation_detailがdictの場合はJSON文字列に変換
        if isinstance(operation_detail, dict):
            operation_detail = json.dumps(operation_detail, ensure_ascii=False)

        sql = """
            INSERT INTO T_ADMIN_AUDIT_LOG (
                audit_log_id,
                user_id,
                user_name,
                operation_type,
                table_name,
                record_id,
                operation_detail,
                operation_timestamp
            ) VALUES (
                SEQ_ADMIN_AUDIT_LOG.NEXTVAL,
                :user_id,
                :user_name,
                :operation_type,
                :table_name,
                :record_id,
                :operation_detail,
                SYSTIMESTAMP
            )
        """

        cursor.execute(sql, {
            'user_id': user_id,
            'user_name': user_name,
            'operation_type': operation_type,
            'table_name': table_name,
            'record_id': str(record_id) if record_id else None,
            'operation_detail': operation_detail
        })
        conn.commit()

        # 挿入されたログIDを取得
        cursor.execute("SELECT SEQ_ADMIN_AUDIT_LOG.CURRVAL FROM DUAL")
        log_id = cursor.fetchone()[0]
        cursor.close()

        return log_id

    @staticmethod
    def get_recent_logs(limit=100, user_id=None, table_name=None):
        """
        最近のログを取得

        Args:
            limit: 取得件数
            user_id: フィルタ用ユーザーID（任意）
            table_name: フィルタ用テーブル名（任意）

        Returns:
            list: ログのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                audit_log_id,
                user_id,
                user_name,
                operation_type,
                table_name,
                record_id,
                operation_detail,
                operation_timestamp
            FROM T_ADMIN_AUDIT_LOG
            WHERE 1=1
        """

        params = {}

        if user_id:
            sql += " AND user_id = :user_id"
            params['user_id'] = user_id

        if table_name:
            sql += " AND table_name = :table_name"
            params['table_name'] = table_name

        sql += " ORDER BY operation_timestamp DESC FETCH FIRST :limit ROWS ONLY"
        params['limit'] = limit

        cursor.execute(sql, params)
        results = dict_factory(cursor)
        cursor.close()

        return results
