"""
API（Ajax用）のルーティング
"""
from flask import Blueprint, jsonify, request
from app.utils.decorators import login_required

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/pulldown_options/<int:pulldown_group_id>')
@login_required
def pulldown_options(pulldown_group_id):
    """プルダウン選択肢を取得"""
    # TODO: データベースから取得
    # 現在はダミーデータ
    options = [
        {'option_value': 'option1', 'option_label': '選択肢1'},
        {'option_value': 'option2', 'option_label': '選択肢2'},
    ]

    return jsonify({'options': options})
