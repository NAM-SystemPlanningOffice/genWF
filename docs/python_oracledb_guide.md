# python-oracledb 使用ガイド

Python 3.13対応のため、従来の cx_Oracle から python-oracledb に移行しました。

## python-oracledb とは

Oracle公式のPython用データベースドライバーで、cx_Oracleの後継です。

### 主な特徴

1. **Thin mode（デフォルト）**
   - Pure Python実装
   - **Oracle Instant Client不要**
   - セットアップが簡単
   - Windows/Linux/macOS対応
   - 通常の用途には十分な性能

2. **Thick mode（オプション）**
   - Oracle Clientライブラリを使用
   - cx_Oracleと同等の機能
   - より高速（大量データ処理時）
   - Oracle Instant Clientが必要

## インストール

### 必要なもの

- Python 3.8以上（本プロジェクトでは3.13使用）
- pip

### インストールコマンド

```bash
pip install oracledb
```

これだけで完了です！Oracle Instant Clientは**不要**です。

## 接続方法

### Thin mode（推奨）

デフォルトでThin modeが使用されます。

```python
import oracledb

connection = oracledb.connect(
    user="NAM_TASK",
    password="your_password",
    dsn="localhost:1521/ORCL"
)
```

### Thick mode

Oracle Instant Clientをインストール済みの環境で使用する場合：

```python
import oracledb

# Thick mode初期化（接続前に1度だけ実行）
oracledb.init_oracle_client(lib_dir="C:/oracle/instantclient_19_21")

# 接続（以降はThin modeと同じ）
connection = oracledb.connect(
    user="NAM_TASK",
    password="your_password",
    dsn="localhost:1521/ORCL"
)
```

本プロジェクトでは `.env` で制御：

```
USE_THICK_MODE=True
```

## cx_Oracle との違い

### API互換性

ほとんどのAPIは互換性があります。

```python
# cx_Oracle
import cx_Oracle
conn = cx_Oracle.connect(user, password, dsn)

# oracledb（同じように使える）
import oracledb
conn = oracledb.connect(user, password, dsn)
```

### 主な変更点

1. **モジュール名**
   ```python
   # 旧: cx_Oracle
   import cx_Oracle
   
   # 新: oracledb
   import oracledb
   ```

2. **例外クラス**
   ```python
   # 旧: cx_Oracle.Error
   except cx_Oracle.Error as e:
       pass
   
   # 新: oracledb.Error
   except oracledb.Error as e:
       pass
   ```

3. **初期化関数**
   ```python
   # 旧: cx_Oracle.init_oracle_client()
   cx_Oracle.init_oracle_client(lib_dir="...")
   
   # 新: oracledb.init_oracle_client()
   oracledb.init_oracle_client(lib_dir="...")
   ```

4. **エンコーディング指定**
   ```python
   # 旧: encodingパラメータ指定
   conn = cx_Oracle.connect(user, password, dsn, encoding="UTF-8")
   
   # 新: デフォルトでUTF-8（指定不要）
   conn = oracledb.connect(user, password, dsn)
   ```

## 本プロジェクトでの使用方法

### 1. 通常の使用（Thin mode - 推奨）

`.env` ファイル:

```
USE_MOCK_DB=False
USE_THICK_MODE=False

ORACLE_DSN=localhost:1521/ORCL
ORACLE_USER=NAM_TASK
ORACLE_PASSWORD=your_password
```

これだけでOK。Oracle Instant Clientは不要です。

### 2. Thick modeの使用

高速化が必要な場合（大量データ処理等）：

#### 2-1. Oracle Instant Clientのインストール

https://www.oracle.com/database/technologies/instant-client/downloads.html

例: `C:\oracle\instantclient_19_21` に解凍

#### 2-2. 環境変数の設定

`.env` ファイル:

```
USE_MOCK_DB=False
USE_THICK_MODE=True

ORACLE_DSN=localhost:1521/ORCL
ORACLE_USER=NAM_TASK
ORACLE_PASSWORD=your_password
```

#### 2-3. app/utils/db.py の編集

`init_db()` 関数内のコメントを解除：

```python
def init_db(app):
    # ...
    
    try:
        import oracledb
        
        # Thick modeを使用する場合
        use_thick = os.environ.get('USE_THICK_MODE', 'False').lower() == 'true'
        if use_thick:
            oracledb.init_oracle_client(lib_dir="C:/oracle/instantclient_19_21")
            app.logger.info("Oracle DB: Using Thick mode")
        else:
            app.logger.info("Oracle DB: Using Thin mode")
```

### 3. モックDBの使用

Oracle DBへの接続が不要な場合（UI開発時等）：

`.env` ファイル:

```
USE_MOCK_DB=True

# 以下は不要
# ORACLE_DSN=...
# ORACLE_USER=...
# ORACLE_PASSWORD=...
```

## パフォーマンス比較

| 項目 | Thin mode | Thick mode |
|------|-----------|------------|
| セットアップ | 簡単（pip installのみ） | 複雑（Oracle Client必要） |
| 接続速度 | 同等 | 同等 |
| クエリ実行 | やや遅い | 速い |
| 大量データ処理 | 遅い | 速い |
| メモリ使用量 | 少ない | 多い |
| 推奨用途 | 通常のWebアプリ | バッチ処理・大量データ |

**結論**: 本プロジェクトのようなWebアプリケーションでは、**Thin modeで十分**です。

## トラブルシューティング

### エラー: `ModuleNotFoundError: No module named 'oracledb'`

**原因**: oracledb がインストールされていない

**解決策**:
```bash
pip install oracledb
```

### エラー: `DPI-1047: Cannot locate a 64-bit Oracle Client library`

**原因**: Thick modeを使用しようとしているが、Oracle Clientが見つからない

**解決策1（推奨）**: Thin modeを使用
```
USE_THICK_MODE=False
```

**解決策2**: Oracle Instant Clientをインストールし、パスを正しく設定

### エラー: `ORA-12541: TNS:no listener`

**原因**: Oracle DBサーバーに接続できない

**解決策**:
1. ORACLE_DSN を確認
2. DBサーバーが起動しているか確認
3. ネットワーク接続を確認
4. ファイアウォールを確認

### 接続が遅い

**Thin modeの場合**:
- 通常のWebアプリには十分な速度
- 気になる場合はThick modeを検討

**Thick modeの場合**:
- ネットワークレイテンシを確認
- コネクションプーリングを検討

## 参考リンク

- 公式ドキュメント: https://python-oracledb.readthedocs.io/
- GitHub: https://github.com/oracle/python-oracledb
- リリースノート: https://python-oracledb.readthedocs.io/en/latest/release_notes.html
- cx_Oracleからの移行ガイド: https://python-oracledb.readthedocs.io/en/latest/user_guide/appendix_c.html

## まとめ

- Python 3.13では **oracledb** を使用
- デフォルトの **Thin mode** で十分（Oracle Client不要）
- セットアップが簡単で、通常のWebアプリには最適
- 必要に応じてThick modeに切り替え可能
- APIは cx_Oracle とほぼ互換
