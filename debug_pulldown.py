"""
プルダウンデータのデバッグスクリプト
"""
from app import create_app
from app.utils.db import get_db_connection, dict_factory

def check_pulldown_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("=== M_PULLDOWN_GROUP ===")
    cursor.execute("SELECT * FROM M_PULLDOWN_GROUP")
    groups = dict_factory(cursor)
    if len(groups) == 0:
        print("(データなし)")
    for group in groups:
        print(group)

    print("\n=== M_PULLDOWN_OPTION ===")
    cursor.execute("SELECT * FROM M_PULLDOWN_OPTION ORDER BY pulldown_group_id, display_order")
    options = dict_factory(cursor)
    if len(options) == 0:
        print("(データなし)")
    for option in options:
        print(option)

    print("\n=== M_APPLICATION_FIELD (field_type='select') ===")
    cursor.execute("SELECT field_id, field_code, field_name, field_type, pulldown_group_id FROM M_APPLICATION_FIELD WHERE field_type = 'select'")
    fields = dict_factory(cursor)
    if len(fields) == 0:
        print("(データなし)")
    for field in fields:
        print(field)

    print("\n=== M_APPLICATION_FIELD (全件) ===")
    cursor.execute("SELECT field_id, application_type_id, field_code, field_name, field_type, pulldown_group_id FROM M_APPLICATION_FIELD ORDER BY application_type_id, display_order")
    all_fields = dict_factory(cursor)
    if len(all_fields) == 0:
        print("(データなし)")
    for field in all_fields:
        print(field)

    cursor.close()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        check_pulldown_data()
