-- ==========================================
-- M_APPLICATION_FIELDテーブルのfield_nameを300バイトに拡張
-- チェックボックスの内容説明を格納できるようにする
-- ==========================================

-- field_nameのサイズを200→300に変更
ALTER TABLE M_APPLICATION_FIELD MODIFY field_name VARCHAR2(300) NOT NULL;

-- 確認
SELECT column_name, data_type, data_length, nullable
FROM user_tab_columns
WHERE table_name = 'M_APPLICATION_FIELD'
  AND column_name = 'FIELD_NAME';
