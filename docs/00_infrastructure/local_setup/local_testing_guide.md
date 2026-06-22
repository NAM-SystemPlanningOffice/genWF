# ローカル環境でのテスト手順

Azure App Service環境がなくても、Flaskの開発サーバーでアプリケーションをテストできます。

## 方法1: Flask開発サーバー + Oracle Database（推奨）

### 前提条件
- Python 3.13
- Oracle Database への接続が可能（社内ネットワーク経由等）
- **Oracle Instant Client は不要**（python-oracledb Thin mode使用）

### 手順

#### 1. Python仮想環境の作成

```bash
cd c:\Users\ootagaki\claude1\genWF
python -m venv venv
venv\Scripts\activate
```

#### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

#### 3. 環境変数の設定

**重要**: python-oracledb (Thin mode) を使用するため、**Oracle Instant Clientは不要**です！

`.env` ファイルを作成:

```bash
copy .env.example .env
```

`.env` を編集（メモ帳で開く）:

```
SECRET_KEY=local-development-secret-key-12345
FLASK_ENV=development

# 社内Oracle DBに接続
ORACLE_DSN=db-server.company.local:1521/ORCL
ORACLE_USER=NAM_TASK
ORACLE_PASSWORD=your-password

ITEMS_PER_PAGE=20
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
```

#### 4. ログディレクトリの作成

```bash
mkdir logs
```

#### 5. データベースのセットアップ（初回のみ）

SQL*Plus または SQL Developer で実行:

```bash
sqlplus NAM_TASK/password@db-server.company.local:1521/ORCL

SQL> @database/01_create_tables.sql
SQL> @database/02_create_foreign_keys.sql
SQL> @database/03_insert_sample_data.sql
SQL> exit
```

#### 6. 開発サーバーの起動

```bash
python run.py
```

以下のように表示されればOK:
```
 * Serving Flask app 'app'
 * Debug mode: on
INFO: Oracle DB: Using python-oracledb (Thin mode by default)
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://0.0.0.0:5000
Press CTRL+C to quit
```

#### 7. ブラウザでアクセス

http://localhost:5000

---

## python-oracledb について

### Thin mode（デフォルト・推奨）

- **Oracle Instant Client不要**
- Pure Python実装
- セットアップが簡単
- 通常のWebアプリには十分な性能

### Thick mode（オプション）

大量データ処理で高速化が必要な場合のみ使用。

1. Oracle Instant Client をインストール
2. `.env` で `USE_THICK_MODE=True` に設定
3. `app/utils/db.py` でパスを指定

**python-oracledb (Thin mode)** を使用します。Oracle Instant Clientのインストールは不要です。

---

## 方法2: Flask開発サーバー + Docker Oracle XE

ローカルにOracle DBがない場合、DockerでOracle XEを起動できます。

### 前提条件
- Docker Desktop がインストール済み

### 手順

#### 1. Docker で Oracle XE を起動

```bash
docker run -d --name oracle-xe ^
  -p 1521:1521 ^
  -e ORACLE_PASSWORD=YourPassword123 ^
  container-registry.oracle.com/database/express:21.3.0-xe
```

起動まで数分かかります。ログを確認:
```bash
docker logs -f oracle-xe
```

`DATABASE IS READY TO USE!` と表示されたらOK。

#### 2. Oracle DB に接続してスキーマを作成

```bash
docker exec -it oracle-xe sqlplus sys/YourPassword123@XE as sysdba

SQL> CREATE USER NAM_TASK IDENTIFIED BY password;
SQL> GRANT CONNECT, RESOURCE TO NAM_TASK;
SQL> GRANT CREATE VIEW TO NAM_TASK;
SQL> GRANT UNLIMITED TABLESPACE TO NAM_TASK;
SQL> EXIT;
```

#### 3. スキーマにログインしてテーブル作成

```bash
docker exec -it oracle-xe sqlplus NAM_TASK/password@XE

SQL> -- ここでDDLを実行
```

または、ホストからファイルを実行:

```bash
docker cp database/01_create_tables.sql oracle-xe:/tmp/
docker cp database/02_create_foreign_keys.sql oracle-xe:/tmp/
docker cp database/03_insert_sample_data.sql oracle-xe:/tmp/

docker exec -it oracle-xe sqlplus NAM_TASK/password@XE @/tmp/01_create_tables.sql
docker exec -it oracle-xe sqlplus NAM_TASK/password@XE @/tmp/02_create_foreign_keys.sql
docker exec -it oracle-xe sqlplus NAM_TASK/password@XE @/tmp/03_insert_sample_data.sql
```

#### 4. .env ファイルを編集

```
ORACLE_DSN=localhost:1521/XE
ORACLE_USER=NAM_TASK
ORACLE_PASSWORD=password
```

#### 5. Flaskサーバーを起動

```bash
python run.py
```

---

## 方法3: モックデータベースでのテスト（DB不要）

Oracle DBへの接続が難しい場合、モックを使用してテストできます。

### テスト用モックの作成

`app/utils/db_mock.py` を作成:

```python
"""
モックデータベース（テスト用）
"""

class MockConnection:
    """モックDB接続"""
    
    def cursor(self):
        return MockCursor()
    
    def commit(self):
        pass
    
    def rollback(self):
        pass
    
    def close(self):
        pass


class MockCursor:
    """モックカーソル"""
    
    def __init__(self):
        self.description = []
        self._results = []
    
    def execute(self, sql, params=None):
        # サンプルデータを返す
        if 'e_imdb2_users' in sql:
            self.description = [
                ('USER_ID',), ('USER_NAME',), 
                ('SHOZOKU',), ('SHOZOKU_FUKUMU',)
            ]
            self._results = [
                ('test_user', 'テストユーザー', '1234000', None)
            ]
        elif 'M_APPLICATION_TYPE' in sql:
            self.description = [
                ('APPLICATION_TYPE_ID',), ('APPLICATION_TYPE_NAME',),
                ('SUPPORT_CREATE',), ('SUPPORT_MODIFY',), ('SUPPORT_DELETE',)
            ]
            self._results = [
                (1, 'Gmailグループ管理', 'Y', 'Y', 'Y')
            ]
    
    def fetchone(self):
        if self._results:
            return self._results[0]
        return None
    
    def fetchall(self):
        return self._results
    
    def close(self):
        pass


def get_mock_db_connection():
    """モックDB接続を取得"""
    return MockConnection()
```

### モックを使用するように設定

`.env` に追加:

```
USE_MOCK_DB=True
```

`app/utils/db.py` を修正:

```python
import os

def get_db_connection():
    """データベース接続を取得"""
    
    # モックDB使用フラグ
    if os.environ.get('USE_MOCK_DB') == 'True':
        from app.utils.db_mock import get_mock_db_connection
        return get_mock_db_connection()
    
    # 通常のOracle接続
    if 'db' not in g:
        # ... 既存のコード
```

---

## 開発時の便利なコマンド

### ログをリアルタイムで確認

PowerShell:
```powershell
Get-Content logs\app.log -Wait -Tail 20
```

コマンドプロンプト:
```cmd
powershell Get-Content logs\app.log -Wait -Tail 20
```

### ポートが使用中の場合

別のポートで起動:

`run.py` を編集:

```python
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8080,  # 5000 → 8080 に変更
        debug=(config_name == 'development')
    )
```

または、環境変数で指定:

```bash
set FLASK_RUN_PORT=8080
python run.py
```

### デバッグモードでの実行

詳細なエラー情報が表示されます（デフォルトで有効）。

`.env`:
```
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

---

## トラブルシューティング

### エラー: `DPI-1047: Cannot locate a 64-bit Oracle Client library`

**原因**: Thick modeを使用しようとしているが、Oracle Clientが見つからない

**解決策1（推奨）**: Thin modeを使用
```
USE_THICK_MODE=False
```

**解決策2**: Oracle Instant Clientをインストールし、パスを設定
1. Oracle Instant Client をインストール
2. `app/utils/db.py` の `init_oracle_client()` でパスを指定
3. `.env` で `USE_THICK_MODE=True`

### エラー: `ORA-12545: Connect failed`

**原因**: Oracle DBに接続できない

**解決策**:
1. `.env` の `ORACLE_DSN` を確認
2. DBサーバーに ping できるか確認
3. ファイアウォールの確認
4. VPN接続が必要な場合は接続

確認方法:
```bash
ping db-server.company.local
telnet db-server.company.local 1521
```

### エラー: `ModuleNotFoundError: No module named 'oracledb'`

**原因**: oracledb がインストールされていない

**解決策**:
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

または直接:
```bash
pip install oracledb
```

### エラー: `ImportError: DLL load failed`

**原因**: Visual C++ Redistributable がインストールされていない

**解決策**:
Microsoft Visual C++ Redistributable をインストール:
https://aka.ms/vs/17/release/vc_redist.x64.exe

### ポート 5000 が使用中

**原因**: 他のアプリケーションがポート5000を使用している

**解決策**:
```bash
# ポートを使用しているプロセスを確認
netstat -ano | findstr :5000

# プロセスを終了（タスクマネージャーで）
# または、別のポートを使用（上記参照）
```

---

## 次のステップ

### 1. 基本的な動作確認

ローカルでサーバーが起動したら:

1. ログイン画面の表示確認
2. データベース接続確認
3. サンプルデータの表示確認

### 2. 機能の段階的実装

1. ログイン機能（ダミー実装でOK）
2. 申請種類一覧の表示
3. 新規申請作成フォーム
4. データベースへの保存

### 3. テストデータの追加

`database/04_insert_test_data.sql` を作成して、テスト用データを追加。

---

## 開発効率を上げるTips

### 自動リロード

ファイルを保存すると自動的にサーバーが再起動します（開発モードの場合）。

### IPythonでのデバッグ

```bash
pip install ipython
```

コード内に追加:
```python
import IPython; IPython.embed()
```

### VSCodeのデバッグ設定

`.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Flask",
            "type": "python",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "run.py",
                "FLASK_ENV": "development"
            },
            "args": [
                "run",
                "--no-debugger",
                "--no-reload"
            ],
            "jinja": true
        }
    ]
}
```

---

## まとめ

ローカル環境でのテストは以下の方法があります:

| 方法 | メリット | デメリット |
|------|---------|-----------|
| Flask開発サーバー + 社内DB | 実際のDBを使用できる | VPN接続が必要な場合あり |
| Flask開発サーバー + Docker Oracle | 完全にローカルで完結 | Docker Desktop が必要 |
| モックDB | DB環境不要で軽量 | 実際のDBとの動作確認不可 |

**推奨**: まずは「方法1」で社内DBに接続してテスト。接続できない場合は「方法2」のDockerを使用。

開発初期段階では「方法3」のモックDBでUI実装を進め、後から実際のDBに接続するのも効率的です。
