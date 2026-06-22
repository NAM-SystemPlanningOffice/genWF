# クイックスタートガイド

Python 3.13 + python-oracledb でローカル環境テストを開始する最短手順です。

## 重要: Oracle Instant Client は不要です！

python-oracledb（Thin mode）を使用するため、**Oracle Instant Clientのインストールは不要**です。
Python 3.13とpipがあれば、すぐに始められます。

## 3つの方法から選択

### 方法A: モックDBで即座にテスト（最速・推奨）
Oracle DBへの接続不要。すぐに動作確認できます。

### 方法B: 実際のOracle DBに接続（推奨）
社内のOracle DBに接続してテストします。**Oracle Instant Client不要**。

### 方法C: Docker Oracle XEを使用
ローカルでOracle DBを起動してテストします。

---

## 方法A: モックDBで即座にテスト（最速）

### 1. セットアップ（初回のみ）

```cmd
cd c:\Users\ootagaki\claude1\genWF
setup_local.bat
```

### 2. 環境変数を編集

`.env` ファイルを開いて以下のように設定:

```
SECRET_KEY=local-test-secret-key-12345
FLASK_ENV=development

# モックDBを使用
USE_MOCK_DB=True

# 以下はモックDB使用時は不要（設定しなくてもOK）
ORACLE_DSN=dummy
ORACLE_USER=dummy
ORACLE_PASSWORD=dummy

ITEMS_PER_PAGE=20
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
```

### 3. サーバー起動

```cmd
start_server.bat
```

または:

```cmd
venv\Scripts\activate
python run.py
```

### 4. ブラウザでアクセス

http://localhost:5000

### モックDBの制限事項

- サンプルデータのみ表示されます
- データの永続化はされません（サーバー再起動で初期化）
- UI動作確認に最適

---

## 方法B: 実際のOracle DBに接続（推奨）

**重要**: python-oracledb (Thin mode) を使用するため、**Oracle Instant Clientは不要**です！

### 1. セットアップ（初回のみ）

```cmd
cd c:\Users\ootagaki\claude1\genWF
setup_local.bat
```

### 2. 環境変数を編集

**Oracle Instant Clientのインストールは不要です！**

`.env` ファイルを開いて実際のDB接続情報を設定:

```
SECRET_KEY=local-test-secret-key-12345
FLASK_ENV=development

# 実際のOracle DBに接続
USE_MOCK_DB=False

# 実際の接続情報
ORACLE_DSN=db-server.company.local:1521/ORCL
ORACLE_USER=NAM_TASK
ORACLE_PASSWORD=your-actual-password

ITEMS_PER_PAGE=20
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
```

### 3. データベースにテーブル作成

SQL*Plus または SQL Developer で:

```sql
sqlplus NAM_TASK/password@db-server.company.local:1521/ORCL

@database/01_create_tables.sql
@database/02_create_foreign_keys.sql
@database/03_insert_sample_data.sql
exit
```

### 4. サーバー起動

```cmd
start_server.bat
```

### 5. ブラウザでアクセス

http://localhost:5000

### 補足: Thin mode と Thick mode

**Thin mode（デフォルト・推奨）**:
- Oracle Instant Client **不要**
- セットアップが簡単
- 通常のWebアプリには十分な性能

**Thick mode（オプション）**:
- Oracle Instant Client **必要**
- より高速（大量データ処理時）
- `.env` で `USE_THICK_MODE=True` に設定

**python-oracledb (Thin mode)** を使用します。Oracle Instant Clientのインストールは不要です。

---

## 方法C: Docker Oracle XEを使用

### 1. Docker Desktop のインストール

https://www.docker.com/products/docker-desktop/

### 2. Oracle XE コンテナを起動

```cmd
docker run -d --name oracle-xe ^
  -p 1521:1521 ^
  -e ORACLE_PASSWORD=MyPassword123 ^
  container-registry.oracle.com/database/express:21.3.0-xe
```

起動まで数分待機（初回は10分程度かかる場合あり）:

```cmd
docker logs -f oracle-xe
```

`DATABASE IS READY TO USE!` と表示されたら Ctrl+C で抜ける。

### 3. スキーマを作成

```cmd
docker exec -it oracle-xe sqlplus sys/MyPassword123@XE as sysdba
```

```sql
CREATE USER NAM_TASK IDENTIFIED BY password;
GRANT CONNECT, RESOURCE TO NAM_TASK;
GRANT CREATE VIEW TO NAM_TASK;
GRANT UNLIMITED TABLESPACE TO NAM_TASK;
EXIT;
```

### 4. テーブルを作成

```cmd
docker cp database/01_create_tables.sql oracle-xe:/tmp/
docker cp database/02_create_foreign_keys.sql oracle-xe:/tmp/
docker cp database/03_insert_sample_data.sql oracle-xe:/tmp/

docker exec -it oracle-xe sqlplus NAM_TASK/password@XE @/tmp/01_create_tables.sql
docker exec -it oracle-xe sqlplus NAM_TASK/password@XE @/tmp/02_create_foreign_keys.sql
docker exec -it oracle-xe sqlplus NAM_TASK/password@XE @/tmp/03_insert_sample_data.sql
```

### 5. セットアップとサーバー起動

```cmd
cd c:\Users\ootagaki\claude1\genWF
setup_local.bat
```

`.env` を編集:

```
SECRET_KEY=local-test-secret-key-12345
FLASK_ENV=development

USE_MOCK_DB=False

ORACLE_DSN=localhost:1521/XE
ORACLE_USER=NAM_TASK
ORACLE_PASSWORD=password

ITEMS_PER_PAGE=20
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
```

```cmd
start_server.bat
```

### 6. ブラウザでアクセス

http://localhost:5000

### Docker コンテナの管理

```cmd
# 停止
docker stop oracle-xe

# 起動
docker start oracle-xe

# 削除
docker rm -f oracle-xe
```

---

## よくある質問

### Q1: setup_local.bat 実行時にエラーが出る

**A**: Pythonがインストールされていない、またはPATHが通っていません。

確認:
```cmd
python --version
```

Python 3.9以上をインストールしてください:
https://www.python.org/downloads/

### Q2: サーバー起動時に `ModuleNotFoundError: No module named 'flask'`

**A**: 仮想環境がアクティブになっていません。

```cmd
venv\Scripts\activate
pip install -r requirements.txt
```

### Q3: Oracle 接続エラー `DPI-1047`

**A**: Thick modeを使用しようとしているが、Oracle Clientが見つかりません。

解決策:
1. **Thin modeを使用**（推奨）: `.env` で `USE_THICK_MODE=False`
2. モックDBを使用（`USE_MOCK_DB=True`）
3. または、Oracle Instant Client をインストールしてThick mode使用

### Q4: ポート 5000 が使用中

**A**: `run.py` を編集してポートを変更:

```python
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8080,  # 5000 → 8080
        debug=(config_name == 'development')
    )
```

### Q5: ブラウザに何も表示されない

**A**: サーバーが起動していない可能性があります。

確認:
```cmd
curl http://localhost:5000
```

ログを確認:
```cmd
type logs\app.log
```

---

## 次のステップ

1. **ログイン機能の実装** - `app/routes/auth.py`
2. **申請一覧画面の実装** - `app/routes/application.py`
3. **承認画面の実装** - `app/routes/approval.py`

詳細は以下を参照:
- [実装サマリ](docs/implementation_summary.md)
- [ローカルテストガイド](docs/local_testing_guide.md)
- [システム設計](docs/system_architecture.md)

---

## サポート

問題が解決しない場合:

1. ログファイルを確認: `logs\app.log`
2. ドキュメントを参照: `docs\*.md`
3. システム企画室に連絡

---

## 推奨フロー（初めての方）

```
1. setup_local.bat を実行
   ↓
2. .env で USE_MOCK_DB=True に設定
   ↓
3. start_server.bat を実行
   ↓
4. http://localhost:5000 にアクセス
   ↓
5. UI動作確認
   ↓
6. 実装を進める
   ↓
7. 実際のDBでテスト（USE_MOCK_DB=False）
```

これで最短5分でローカルテスト環境が整います！
