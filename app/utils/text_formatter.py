"""
テキスト書式変換ユーティリティ
"""
import re
from markupsafe import Markup, escape


def format_help_text(text):
    """
    ヘルプテキストを簡易的にHTMLに変換

    対応書式:
    - 改行 → <br>
    - URLリンク: https://... または http://... → クリック可能なリンク

    Args:
        text: 入力テキスト

    Returns:
        Markup: HTMLセーフな変換済みテキスト

    例:
        入力: "詳細はこちら\\nhttps://example.com/manual\\n担当部署に確認"
        出力: "詳細はこちら<br><a href=\"https://example.com/manual\" target=\"_blank\" rel=\"noopener noreferrer\">https://example.com/manual</a><br>担当部署に確認"
    """
    if not text:
        return ''

    # エスケープ（XSS対策）
    text = escape(text)

    # 改行を<br>に変換
    text = str(text).replace('\n', '<br>')

    # URLをリンクに変換（https:// および http://）
    # target="_blank"で新しいタブで開く
    # rel="noopener noreferrer"でセキュリティ対策
    url_pattern = r'(https?://[^\s<>"]+)'
    text = re.sub(
        url_pattern,
        r'<a href="\1" target="_blank" rel="noopener noreferrer" style="color: #3498db; text-decoration: underline;">\1</a>',
        text
    )

    return Markup(text)
