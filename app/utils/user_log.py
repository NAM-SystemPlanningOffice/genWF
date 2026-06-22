"""
ユーザー操作ログ記録ユーティリティ
"""
from datetime import datetime
from app.utils.db import get_db_connection


def log_user_action(user_id, action_type, application_id=None, application_type_code=None, node_name=None):
    """
    ユーザーアクションをログに記録

    Args:
        user_id: 操作ユーザーID
        action_type: アクション種別（save_draft/submit/withdraw/approve/return/reject/recall）
        application_id: 申請ID（任意）
        application_type_code: 申請種類コード（任意）
        node_name: ワークフローノード名（任意）

    Returns:
        int: ログID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # シーケンスから新しいIDを取得
        cursor.execute("SELECT SEQ_USER_LOG.NEXTVAL FROM DUAL")
        log_id = cursor.fetchone()[0]

        # ログを挿入
        sql = """
            INSERT INTO T_USER_LOG (
                log_id,
                user_id,
                application_id,
                application_type_code,
                node_name,
                action_type,
                action_timestamp
            ) VALUES (
                :log_id,
                :user_id,
                :application_id,
                :application_type_code,
                :node_name,
                :action_type,
                SYSTIMESTAMP
            )
        """

        cursor.execute(sql, {
            'log_id': log_id,
            'user_id': user_id,
            'application_id': application_id,
            'application_type_code': application_type_code,
            'node_name': node_name,
            'action_type': action_type
        })

        conn.commit()
        cursor.close()

        return log_id

    except Exception as e:
        conn.rollback()
        cursor.close()
        # ログ記録失敗時は例外を上げず、エラーをログ出力のみ
        from flask import current_app
        current_app.logger.error(f'ユーザー操作ログ記録エラー: {str(e)}')
        return None
