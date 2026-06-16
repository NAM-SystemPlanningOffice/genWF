# 画面イメージテスト クイックスタート

## HTMLファイルの保存先

```
c:\Users\ootagaki\claude1\genWF\test_results\html\
```

**現在の状態**: まだディレクトリが作成されていません（テスト未実行）

---

## 📍 HTMLファイルを作成する手順

### ステップ1: テストを実行

以下のいずれかの方法でテストを実行してください：

#### 方法A: バッチファイルで実行（最も簡単）

```bash
# プロジェクトルートで実行
run_visual_tests.bat
```

#### 方法B: コマンドで実行

```bash
# 仮想環境を有効化
venv\Scripts\activate

# 画面イメージテストを実行
pytest -m visual -v -s
```

#### 方法C: 特定のテストのみ実行

```bash
# ログイン画面のみ
pytest tests/integration/test_visual_html.py::TestVisualHTML::test_login_page_html -v -s

# 申請一覧画面のみ
pytest tests/integration/test_visual_html.py::TestVisualHTML::test_application_list_html -v -s
```

---

### ステップ2: HTMLファイルの確認

テスト実行後、以下の場所にHTMLファイルが作成されます：

```
c:\Users\ootagaki\claude1\genWF\test_results\html\
├── 01_login_page.html
├── 02_application_list.html
├── 03_application_create.html
├── 04_approval_tasks.html
├── 05_approval_task_detail.html
├── 06_admin_page.html
└── 90_error_404.html
```

---

### ステップ3: ブラウザで開く

#### Windowsエクスプローラーで開く

```bash
# エクスプローラーで開く
explorer test_results\html

# または
start test_results\html
```

#### 特定のHTMLファイルをブラウザで開く

```bash
# 申請一覧画面を開く
start test_results\html\02_application_list.html

# ログイン画面を開く
start test_results\html\01_login_page.html
```

---

## 🎯 最も簡単な実行方法

### ワンステップで実行

```bash
# これだけ実行すれば全部完了
run_visual_tests.bat
```

このバッチファイルは以下を自動実行します：
1. ✅ `test_results\html` ディレクトリを作成
2. ✅ 画面イメージテストを実行
3. ✅ HTMLファイルを保存
4. ✅ エクスプローラーで自動的に開く

---

## 📋 実行例

### コマンドプロンプトでの実行

```cmd
C:\Users\ootagaki\claude1\genWF> run_visual_tests.bat

================================
画面イメージテスト実行
================================

テスト画面のHTMLを保存します
保存先: test_results\html\

テスト実行中...

tests/integration/test_visual_html.py::TestVisualHTML::test_login_page_html
✅ HTML保存: test_results\html\01_login_page.html
PASSED

tests/integration/test_visual_html.py::TestVisualHTML::test_application_list_html
✅ HTML保存: test_results\html\02_application_list.html
PASSED

...（省略）

================================
テスト完了
================================

保存された画面HTMLファイル:
01_login_page.html
02_application_list.html
03_application_create.html
04_approval_tasks.html
05_approval_task_detail.html
06_admin_page.html
90_error_404.html

HTMLファイルをブラウザで開いて確認してください
例: start test_results\html\02_application_list.html

（エクスプローラーが自動的に開きます）
```

---

## 🔍 トラブルシューティング

### 問題1: `pytest` コマンドが見つからない

**原因**: 仮想環境が有効化されていない

**解決方法**:
```bash
# 仮想環境を有効化
venv\Scripts\activate

# プロンプトが (venv) になることを確認
(venv) C:\Users\ootagaki\claude1\genWF>

# 再度テスト実行
pytest -m visual -v
```

---

### 問題2: テストが失敗する

**原因**: 依存パッケージが不足している可能性

**解決方法**:
```bash
# 仮想環境を有効化
venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# 再度テスト実行
pytest -m visual -v
```

---

### 問題3: HTMLファイルが空または文字化け

**原因**: エンコーディングの問題

**確認方法**:
```bash
# HTMLファイルのサイズを確認
dir test_results\html\*.html

# 0バイトでなければOK
```

**解決方法**: テストを再実行

---

### 問題4: ディレクトリが作成されない

**原因**: 権限の問題またはパスの問題

**解決方法**:
```bash
# 手動でディレクトリを作成
mkdir test_results
mkdir test_results\html

# 再度テスト実行
pytest -m visual -v
```

---

## 📂 ファイル構成

```
c:\Users\ootagaki\claude1\genWF\
├── run_visual_tests.bat          ← これを実行
├── tests/
│   └── integration/
│       └── test_visual_html.py   ← テストコード
└── test_results/                 ← テスト実行後に作成される
    └── html/                     ← HTMLファイルの保存先
        ├── 01_login_page.html
        ├── 02_application_list.html
        ├── 03_application_create.html
        ├── 04_approval_tasks.html
        ├── 05_approval_task_detail.html
        ├── 06_admin_page.html
        └── 90_error_404.html
```

---

## 🎯 次のステップ

### 1. テストを実行してHTMLを生成

```bash
run_visual_tests.bat
```

### 2. HTMLファイルを確認

```bash
# エクスプローラーで開く（自動）
explorer test_results\html
```

### 3. ブラウザで画面を確認

ファイルをダブルクリックしてブラウザで開く

---

## 💡 Tips

### 毎回自動的にブラウザで開く

`run_visual_tests.bat` の最後に以下を追加：

```batch
REM 申請一覧画面を自動的に開く
start test_results\html\02_application_list.html
```

### 特定の画面のみテスト

```bash
# ログイン画面のみ
pytest tests/integration/test_visual_html.py::TestVisualHTML::test_login_page_html -v -s

# 申請一覧と申請作成のみ
pytest tests/integration/test_visual_html.py::TestVisualHTML::test_application_list_html tests/integration/test_visual_html.py::TestVisualHTML::test_application_create_html -v -s
```

### HTMLファイルを削除して再実行

```bash
# 古いHTMLファイルを削除
del /Q test_results\html\*.html

# 再実行
run_visual_tests.bat
```

---

## まとめ

### 📍 HTMLファイルの場所

```
c:\Users\ootagaki\claude1\genWF\test_results\html\
```

### 🚀 最速の実行方法

```bash
run_visual_tests.bat
```

### ✅ 確認方法

```bash
explorer test_results\html
```

これでHTMLファイルが作成され、ブラウザで画面を確認できます！
