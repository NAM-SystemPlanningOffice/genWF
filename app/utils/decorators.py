"""
デコレーター関数
"""
from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """
    ログイン必須デコレーター

    Args:
        f: デコレート対象の関数

    Returns:
        function: ラップされた関数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('ログインが必要です', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    管理者権限必須デコレーター

    Args:
        f: デコレート対象の関数

    Returns:
        function: ラップされた関数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('ログインが必要です', 'error')
            return redirect(url_for('auth.login'))

        if not session.get('is_admin'):
            flash('管理者権限が必要です', 'error')
            return redirect(url_for('application.index'))

        return f(*args, **kwargs)
    return decorated_function
