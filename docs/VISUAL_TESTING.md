# 画面イメージでテスト結果を確認する方法

## 概要

このドキュメントでは、テスト実行時に画面イメージ（HTML、スクリーンショット）を保存・確認する方法を説明します。

---

## 方法1: HTMLレスポンスを保存（簡単・推奨）

### 仕組み

Flaskのtest clientは実際のHTMLを返すので、それをファイルに保存してブラウザで開けます。

### 実装

すでに実装済みのフィクスチャを使用します。

#### テストコード例

```python
def test_application_list_with_html_save(auth_client, save_html):
    """申請一覧画面のHTMLを保存"""
    response = auth_client.get('/application/')
    
    # HTMLを保存
    save_html(response, 'application_list.html')
    
    assert response.status_code == 200
```

#### 保存されるHTML

- 保存先: `test_results/html/application_list.html`
- ブラウザで開いて確認可能

---

## 方法2: Seleniumでスクリーンショット撮影（高機能）

### 仕組み

実際のブラウザを起動して、画面のスクリーンショットを撮影します。

### セットアップ

```bash
# Seleniumとドライバーをインストール
pip install selenium pytest-selenium
pip install webdriver-manager

# requirements.txtに追加
echo selenium >> requirements.txt
echo pytest-selenium >> requirements.txt
echo webdriver-manager >> requirements.txt
```

### 使い方

すでに実装済みのSeleniumテストを使用します。

```bash
# Seleniumテストを実行
pytest -m selenium --cov=app -v

# スクリーンショットは test_results/screenshots/ に保存される
```

---

## 方法3: pytest-htmlでレポート生成（包括的）

### 仕組み

テスト結果をHTMLレポートにまとめ、スクリーンショットも埋め込みます。

### セットアップ

```bash
# pytest-htmlをインストール
pip install pytest-html

# requirements.txtに追加
echo pytest-html >> requirements.txt
```

### 使い方

```bash
# HTMLレポート付きでテスト実行
pytest --html=test_results/report.html --self-contained-html

# レポートをブラウザで開く
start test_results/report.html  # Windows
```

---

## 実装詳細

### 1. HTMLレスポンス保存フィクスチャ

すでに `tests/conftest.py` に実装されています：

```python
import os
from datetime import datetime

@pytest.fixture(scope='function')
def save_html(request):
    """HTMLレスポンスを保存するヘルパー"""
    output_dir = 'test_results/html'
    os.makedirs(output_dir, exist_ok=True)
    
    def _save(response, filename=None):
        if filename is None:
            # テスト名から自動生成
            test_name = request.node.name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{test_name}_{timestamp}.html'
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.get_data(as_text=True))
        
        print(f'\n✅ HTML保存: {filepath}')
        return filepath
    
    return _save


@pytest.fixture(scope='function')
def save_screenshot():
    """スクリーンショットを保存するヘルパー"""
    output_dir = 'test_results/screenshots'
    os.makedirs(output_dir, exist_ok=True)
    
    def _save(driver, filename):
        filepath = os.path.join(output_dir, filename)
        driver.save_screenshot(filepath)
        print(f'\n✅ スクリーンショット保存: {filepath}')
        return filepath
    
    return _save
```

---

### 2. Seleniumテストの実装

`tests/e2e/test_visual.py` を作成します：

```python
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture(scope='function')
def driver():
    """Seleniumドライバー"""
    from selenium.webdriver.chrome.options import Options
    
    options = Options()
    options.add_argument('--headless')  # ヘッドレスモード
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


@pytest.mark.selenium
@pytest.mark.slow
class TestVisualScreenshots:
    """画面スクリーンショットテスト"""
    
    def test_login_page_screenshot(self, driver, save_screenshot):
        """ログイン画面のスクリーンショット"""
        driver.get('http://localhost:5000/auth/login')
        
        # ページ読み込み待機
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # スクリーンショット保存
        save_screenshot(driver, 'login_page.png')
        
        assert 'login' in driver.page_source.lower()
    
    def test_application_list_screenshot(self, driver, save_screenshot):
        """申請一覧画面のスクリーンショット"""
        # ログイン（開発環境）
        driver.get('http://localhost:5000/auth/login')
        
        # ユーザーID入力
        user_id_input = driver.find_element(By.NAME, 'user_id')
        user_id_input.send_keys('test_user')
        
        # ログインボタンクリック
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()
        
        # 所属選択（自動リダイレクト or 選択画面）
        WebDriverWait(driver, 10).until(
            EC.url_contains('/application')
        )
        
        # スクリーンショット保存
        save_screenshot(driver, 'application_list.png')
        
        assert '/application' in driver.current_url
```

---

## 使用方法

### パターン1: HTMLのみ保存（最も簡単）

```python
# tests/integration/test_visual_html.py

@pytest.mark.visual
def test_all_pages_html(auth_client, save_html):
    """主要画面のHTMLを保存"""
    
    # 1. 申請一覧
    response = auth_client.get('/application/')
    save_html(response, '01_application_list.html')
    
    # 2. 申請作成画面
    response = auth_client.get('/application/create/1')
    save_html(response, '02_application_create.html')
    
    # 3. 承認タスク一覧
    response = auth_client.get('/approval/tasks')
    save_html(response, '03_approval_tasks.html')
```

実行：
```bash
pytest -m visual -v

# 結果確認
start test_results/html/01_application_list.html
```

---

### パターン2: スクリーンショット撮影（ブラウザ必要）

#### 前提条件

```bash
# 開発サーバーを起動
python run.py
# 別のターミナルでテスト実行
```

実行：
```bash
pytest -m selenium -v

# 結果確認
start test_results/screenshots/login_page.png
```

---

### パターン3: HTMLレポート生成（全テスト結果）

```bash
# レポート付きで全テスト実行
pytest --html=test_results/report.html --self-contained-html --cov=app

# レポートをブラウザで開く
start test_results/report.html
```

---

## 実行スクリプト

### `run_visual_tests.bat` を作成

```batch
@echo off
echo ================================
echo 画面イメージテスト実行
echo ================================

REM 出力ディレクトリ作成
if not exist "test_results\html" mkdir test_results\html
if not exist "test_results\screenshots" mkdir test_results\screenshots

REM 仮想環境を有効化
call venv\Scripts\activate

echo.
echo [1/2] HTMLレスポンステスト実行中...
pytest -m visual -v -s

echo.
echo [2/2] HTMLレポート生成中...
pytest --html=test_results/report.html --self-contained-html

echo.
echo ================================
echo テスト完了
echo ================================
echo.
echo 結果を確認:
echo - HTML: test_results\html\
echo - レポート: test_results\report.html
echo.

REM 自動的にレポートを開く
start test_results\report.html

pause
```

---

## テスト結果の確認方法

### 1. 保存されたHTML確認

```bash
# エクスプローラーで開く
explorer test_results\html

# 特定のHTMLをブラウザで開く
start test_results\html\application_list.html
```

### 2. スクリーンショット確認

```bash
# エクスプローラーで開く
explorer test_results\screenshots

# 特定の画像を開く
start test_results\screenshots\login_page.png
```

### 3. HTMLレポート確認

```bash
# ブラウザで開く
start test_results\report.html
```

HTMLレポートには以下が含まれます：
- ✅ テスト結果サマリー
- ✅ 各テストの成功/失敗
- ✅ エラーメッセージ
- ✅ 実行時間
- ✅ カバレッジ情報（別途生成が必要）

---

## よくある質問

### Q1: CSSやJavaScriptは反映される？

**HTMLのみ保存の場合**:
- CSS: ✅ 反映される（外部CSSは相対パスが必要）
- JavaScript: ❌ 動作しない（静的HTMLのみ）

**Seleniumスクリーンショットの場合**:
- CSS: ✅ 完全に反映される
- JavaScript: ✅ 実行後の状態をキャプチャ

### Q2: 開発サーバーを起動する必要がある？

**HTMLのみ保存**: ❌ 不要（test clientが仮想サーバー）
**Seleniumテスト**: ✅ 必要（実際のブラウザがアクセス）

### Q3: 画像が表示されない

保存されたHTMLでは、相対パスの画像が表示されない場合があります。

**対策**:
```python
# 絶対パスに変換するヘルパー
def fix_static_paths(html_content):
    import re
    # /static/... を file:///path/to/static/... に変換
    base_path = os.path.abspath('app/static')
    html_content = re.sub(
        r'src="/static/',
        f'src="file:///{base_path}/',
        html_content
    )
    return html_content

# 使用例
html = response.get_data(as_text=True)
html = fix_static_paths(html)
save_html(html, 'page.html')
```

---

## 比較表

| 方法 | 簡単さ | 実際の見た目 | 動作確認 | サーバー起動 |
|------|--------|------------|---------|------------|
| **HTML保存** | ⭐⭐⭐ | 🟡 静的 | ❌ | 不要 |
| **Selenium** | ⭐⭐ | ✅ 完全 | ✅ | 必要 |
| **HTMLレポート** | ⭐⭐⭐ | 🟡 テキスト | ❌ | 不要 |

---

## 推奨ワークフロー

### 日常開発

```bash
# HTMLのみ保存（高速）
pytest -m visual -v
start test_results\html\application_list.html
```

### 重要な変更前

```bash
# 開発サーバー起動
python run.py

# 別ターミナルでSeleniumテスト
pytest -m selenium -v
```

### リリース前

```bash
# 全テスト + HTMLレポート
pytest --html=test_results/report.html --self-contained-html
start test_results\report.html
```

---

## まとめ

### ✅ 実装済み機能

1. **HTML保存フィクスチャ** - `save_html(response, filename)`
2. **スクリーンショット保存フィクスチャ** - `save_screenshot(driver, filename)`
3. **HTMLレポート生成** - `pytest-html`

### 🎯 最も簡単な方法

```python
def test_my_page(auth_client, save_html):
    response = auth_client.get('/application/')
    save_html(response, 'my_page.html')
    # → test_results/html/my_page.html に保存
```

```bash
start test_results\html\my_page.html
```

これで、ブラウザで実際の画面イメージを確認できます！
