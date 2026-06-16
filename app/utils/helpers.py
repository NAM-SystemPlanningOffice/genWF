"""
ヘルパー関数
"""
from datetime import datetime


def format_date(value, format='%Y/%m/%d %H:%M'):
    """
    日時をフォーマット

    Args:
        value: 日時（datetime、str、None）
        format: フォーマット文字列

    Returns:
        str: フォーマット済み日時文字列
    """
    if value is None:
        return ''

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value

    if isinstance(value, datetime):
        return value.strftime(format)

    return str(value)


def format_status(status):
    """
    ステータスを日本語に変換

    Args:
        status: ステータスコード

    Returns:
        str: 日本語のステータス名
    """
    status_map = {
        'draft': '下書き',
        'submitted': '申請中',
        'approved': '承認済み',
        'rejected': '却下',
        'withdrawn': '取り下げ',
        'in_progress': '進行中',
        'completed': '完了',
        'waiting': '待機中',
        'pending': '承認待ち',
        'skipped': 'スキップ'
    }
    return status_map.get(status, status)


def format_action_type(action_type):
    """
    申請区分を日本語に変換

    Args:
        action_type: 申請区分コード

    Returns:
        str: 日本語の申請区分名
    """
    action_map = {
        'create': '新規作成',
        'modify': '修正',
        'delete': '削除'
    }
    return action_map.get(action_type, action_type)


def format_node_type(node_type):
    """
    ノード種別を日本語に変換

    Args:
        node_type: ノード種別コード

    Returns:
        str: 日本語のノード種別名
    """
    node_type_map = {
        'applicant_dept': '申請者所属',
        'jurisdiction_dept': '所管所属',
        'specific_dept': '特定所属',
        'final': '最終承認',
        'report': '報告'
    }
    return node_type_map.get(node_type, node_type)


def get_urgency_level(days_pending):
    """
    経過日数から緊急度を判定

    Args:
        days_pending: 経過日数

    Returns:
        tuple: (緊急度レベル, ラベル, CSSクラス)
    """
    if days_pending >= 7:
        return ('high', '遅延', 'danger')
    elif days_pending >= 3:
        return ('medium', '注意', 'warning')
    else:
        return ('low', '正常', 'success')
