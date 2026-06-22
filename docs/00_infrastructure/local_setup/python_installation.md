# Python 3.13 インストールガイド

このプロジェクトはPython 3.13を使用します。

> **技術仕様**: Python 3.13を使用する理由や詳細は [../../reference/TECH_SPECS.md](../../reference/TECH_SPECS.md) を参照してください。

## Windows でのインストール方法

### 方法1: 公式サイトからインストール（推奨）

#### 1. ダウンロード

https://www.python.org/downloads/

「Download Python 3.13.x」ボタンをクリック

#### 2. インストール

1. ダウンロードした `python-3.13.x-amd64.exe` を実行
2. **重要**: 「Add Python 3.13 to PATH」に**必ずチェック**を入れる
3. 「Install Now」をクリック
4. インストール完了まで待機

#### 3. 確認

コマンドプロンプトまたはPowerShellで:

```cmd
python --version
```

または:

```cmd
py -3.13 --version
```

`Python 3.13.x` と表示されればOK

---

### 方法2: Microsoft Store からインストール

#### 1. Microsoft Store を開く

Windows キー → 「Microsoft Store」と入力

#### 2. Python 3.13 を検索

「Python 3.13」で検索

#### 3. インストール

「入手」または「インストール」をクリック

#### 4. 確認

```cmd
python3.13 --version
```

---

### 方法3: winget でインストール

PowerShellまたはコマンドプロンプト（管理者権限）で:

```powershell
winget install Python.Python.3.13
```

---

## 複数バージョンの管理

### Python Launcher を使用

Windows版Pythonには `py` コマンド（Python Launcher）が含まれています。

#### インストール済みバージョンの確認

```cmd
py --list
```

出力例:
```
 -V:3.13          Python 3.13.0
 -V:3.12          Python 3.12.0
```

#### 特定バージョンの実行

```cmd
# Python 3.13 を実行
py -3.13 --version

# Python 3.13 で仮想環境を作成
py -3.13 -m venv venv

# Python 3.13 でスクリプトを実行
py -3.13 script.py
```

---

## トラブルシューティング

### `python` コマンドが見つからない

**原因**: PATHが通っていない

**解決策**:

1. インストール時に「Add Python to PATH」をチェックし忘れた
2. 手動でPATHを追加:
   - システム環境変数を開く
   - `Path` 変数に以下を追加:
     ```
     C:\Users\<ユーザー名>\AppData\Local\Programs\Python\Python313
     C:\Users\<ユーザー名>\AppData\Local\Programs\Python\Python313\Scripts
     ```
3. または、`py -3.13` を使用

### 複数バージョンがインストールされている

**`py` コマンドを使用して明示的にバージョン指定**:

```cmd
# Python 3.13 を使用
py -3.13 -m venv venv
venv\Scripts\activate
```

### `pip` が見つからない

仮想環境内で実行してください:

```cmd
venv\Scripts\activate
pip --version
```

または:

```cmd
py -3.13 -m pip --version
```

---

## 本プロジェクトでの使用

### セットアップスクリプト

#### 標準版（Python 3.13が必須）

```cmd
setup_local.bat
```

`py -3.13` コマンドを使用します。

#### 自動検出版（どのコマンドでもOK）

```cmd
setup_local_advanced.bat
```

以下の順序で自動検出:
1. `py -3.13`
2. `python3.13`
3. `python`（バージョン確認）

---

## 推奨事項

### 1. クリーンインストール

他のPythonバージョンがない状態で、Python 3.13のみをインストールするのが最もシンプルです。

### 2. 公式サイトからインストール

Microsoft Storeやwingetよりも、公式サイトからのインストールが確実です。

### 3. PATHに追加

必ず「Add Python to PATH」をチェックしてインストールしてください。

### 4. 仮想環境を使用

プロジェクトごとに仮想環境を作成することで、依存関係の競合を避けられます。

```cmd
py -3.13 -m venv venv
venv\Scripts\activate
```

---

## よくある質問

### Q1: Python 3.12 以前のバージョンでも動作しますか？

A: python-oracledb は Python 3.8以上で動作しますが、このプロジェクトは**Python 3.13を推奨**しています。

### Q2: 既存のPython環境を残したまま 3.13 を追加できますか？

A: はい。複数バージョンを共存させ、`py -3.13` で使い分けできます。

### Q3: Anaconda を使っていますが？

A: Anaconda環境でも動作しますが、標準のPython 3.13を推奨します。

```cmd
# Anaconda で Python 3.13 環境を作成
conda create -n genWF python=3.13
conda activate genWF
pip install -r requirements.txt
```

### Q4: WSL（Windows Subsystem for Linux）でも使えますか？

A: はい。Ubuntu等のWSL環境でも動作します。

```bash
# WSL (Ubuntu) でのインストール
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 確認コマンド集

```cmd
REM Pythonバージョン確認
python --version
py -3.13 --version

REM インストール先確認
where python
py -3.13 -c "import sys; print(sys.executable)"

REM pipバージョン確認
pip --version
py -3.13 -m pip --version

REM インストール済みパッケージ確認
pip list

REM oracledb がインストールされているか確認
pip show oracledb
```

---

## 参考リンク

- Python 公式: https://www.python.org/downloads/
- Python 3.13 リリースノート: https://docs.python.org/3.13/whatsnew/3.13.html
- Windows での Python: https://docs.python.org/3/using/windows.html
- Python Launcher: https://docs.python.org/3/using/windows.html#python-launcher-for-windows

---

## まとめ

1. **Python 3.13 をインストール**（公式サイト推奨）
2. **「Add Python to PATH」をチェック**
3. `py -3.13 --version` で確認
4. `setup_local.bat` を実行
5. 完了！

インストールでお困りの場合は、システム企画室までご連絡ください。
