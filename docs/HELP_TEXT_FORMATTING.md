# ヘルプテキストの書式設定

## 概要

help_textフィールドで改行やURLリンクを使用する方法。

---

## 方法1: 改行のみ対応（シンプル）

### 実装

CSSで`white-space: pre-line`を設定。

```css
.help-text {
    white-space: pre-line;
}
```

### 入力方法

管理画面のhelp_textテキストエリアで**Enterキーで改行**を入力：

```
1行目の説明
2行目の説明
3行目の説明
```

### 表示結果

```
1行目の説明
2行目の説明
3行目の説明
```

### メリット・デメリット

✅ シンプル、セキュリティ安全  
❌ URLリンクは不可（テキストとして表示）

---

## 方法2: 簡易Markdown対応（改行＋URLリンク）

### 実装

Pythonでhelp_textを簡易的にHTMLに変換。

#### app/utils/text_formatter.py（新規作成）

```python
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
    - URLリンク: https://... → <a href="..." target="_blank">...</a>
    
    Args:
        text: 入力テキスト
    
    Returns:
        Markup: HTMLセーフな変換済みテキスト
    """
    if not text:
        return ''
    
    # エスケープ（XSS対策）
    text = escape(text)
    
    # 改行を<br>に変換
    text = text.replace('\n', '<br>')
    
    # URLをリンクに変換（https:// および http://）
    url_pattern = r'(https?://[^\s<>"]+)'
    text = re.sub(url_pattern, r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', text)
    
    return Markup(text)
```

#### テンプレート側の変更

```jinja
{% if field.help_text %}
<span class="help-text">{{ field.help_text | format_help_text | safe }}</span>
{% endif %}
```

#### Jinjaフィルタの登録（app/__init__.py）

```python
from app.utils.text_formatter import format_help_text

def create_app():
    # ...既存のコード...
    
    # カスタムフィルタを登録
    app.jinja_env.filters['format_help_text'] = format_help_text
    
    return app
```

### 入力方法

管理画面のhelp_textに以下のように入力：

```
詳細はこちらを参照してください
https://example.com/manual
担当部署に確認が必要です
```

### 表示結果

```
詳細はこちらを参照してください
https://example.com/manual （←クリック可能なリンク）
担当部署に確認が必要です
```

### メリット・デメリット

✅ 改行とURLリンク両方対応  
✅ XSS対策済み（エスケープ処理あり）  
❌ やや複雑

---

## 方法3: 完全なMarkdown対応（高機能）

### 実装

markdownライブラリを使用。

```bash
pip install markdown
```

```python
import markdown
from markupsafe import Markup

def format_help_text_markdown(text):
    """Markdownを完全サポート"""
    if not text:
        return ''
    
    # Markdown変換
    html = markdown.markdown(
        text,
        extensions=['nl2br', 'sane_lists']
    )
    
    return Markup(html)
```

### 入力方法

Markdown記法で入力：

```markdown
**重要**: 所属長の承認が必要です

詳細は以下を参照:
- [マニュアル](https://example.com/manual)
- [FAQ](https://example.com/faq)

問い合わせ: support@example.com
```

### 表示結果

- 太字、リンク、リスト、メールアドレスリンクなど全て対応

### メリット・デメリット

✅ 高機能（太字、リスト、リンクなど）  
❌ 最も複雑  
❌ 入力者がMarkdown記法を知る必要がある

---

## 推奨

### 一般的な用途
**方法2: 簡易Markdown対応**を推奨

- 改行とURLリンクが使える
- セキュリティ安全
- 入力が簡単（Markdown記法不要）

### シンプルでOKな場合
**方法1: 改行のみ対応**

- 実装が最もシンプル
- URLリンクが不要な場合に適している
