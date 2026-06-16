"""
申請詳細データモデル（EAVモデル）
"""
from datetime import datetime
from app.utils.db import get_db_connection, dict_factory


class ApplicationDetail:
    """申請詳細モデル"""

    @staticmethod
    def save_details(application_id, field_values):
        """
        申請詳細データを保存

        Args:
            application_id: 申請ID
            field_values: フィールド値のリスト
                [
                    {
                        'detail_seq': 1,
                        'field_id': 1,
                        'field_value': 'value1'
                    },
                    ...
                ]

        Returns:
            int: 保存した件数
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        now = datetime.now()

        sql = """
            INSERT INTO T_APPLICATION_DETAIL (
                detail_id,
                application_id,
                detail_seq,
                field_id,
                field_value,
                field_value_large,
                field_label,
                detail_action,
                created_at,
                updated_at
            ) VALUES (
                SEQ_APPLICATION_DETAIL.NEXTVAL,
                :application_id,
                :detail_seq,
                :field_id,
                :field_value,
                :field_value_large,
                :field_label,
                :detail_action,
                :created_at,
                :updated_at
            )
        """

        count = 0
        for field_value in field_values:
            value = field_value.get('field_value', '')

            # 値を文字列に変換（数値型やNoneの場合に対応）
            if value is None:
                value = ''
            elif not isinstance(value, str):
                value = str(value)

            # 値が4000文字を超える場合はfield_value_largeに格納
            if len(value) > 4000:
                field_value_col = None
                field_value_large_col = value
            else:
                field_value_col = value
                field_value_large_col = None

            params = {
                'application_id': application_id,
                'detail_seq': field_value.get('detail_seq', 1),
                'field_id': field_value['field_id'],
                'field_value': field_value_col,
                'field_value_large': field_value_large_col,
                'field_label': field_value.get('field_label'),
                'detail_action': field_value.get('detail_action', 'add'),
                'created_at': now,
                'updated_at': now
            }

            cursor.execute(sql, params)
            count += 1

        conn.commit()
        cursor.close()

        return count

    @staticmethod
    def get_by_application(application_id):
        """
        申請IDから申請詳細データを取得

        Args:
            application_id: 申請ID

        Returns:
            list: 申請詳細のリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                d.detail_id,
                d.application_id,
                d.detail_seq,
                d.field_id,
                CASE
                    WHEN d.field_value IS NOT NULL THEN d.field_value
                    ELSE TO_CHAR(d.field_value_large)
                END AS field_value,
                d.field_label,
                d.detail_action,
                f.field_code,
                f.field_name,
                f.field_type,
                f.is_visible
            FROM T_APPLICATION_DETAIL d
            INNER JOIN M_APPLICATION_FIELD f
                ON d.field_id = f.field_id
            WHERE d.application_id = :application_id
            ORDER BY d.detail_seq, f.display_order
        """

        cursor.execute(sql, {'application_id': application_id})
        results = dict_factory(cursor)

        cursor.close()

        return results

    @staticmethod
    def get_grouped_by_seq(application_id):
        """
        申請IDから申請詳細データをdetail_seqでグループ化して取得

        Args:
            application_id: 申請ID

        Returns:
            dict: detail_seqをキーとした申請詳細の辞書
                {
                    1: [
                        {'field_code': 'email', 'field_value': 'test@example.com'},
                        {'field_code': 'name', 'field_value': 'Test Group'}
                    ],
                    2: [...]
                }
        """
        details = ApplicationDetail.get_by_application(application_id)

        grouped = {}
        for detail in details:
            # 非表示フィールドは除外
            if detail.get('is_visible') != 'Y':
                continue

            # detail_actionがNone、'none'、'readonly'のレコードは除外
            detail_action = detail.get('detail_action')
            if detail_action is None or detail_action in ('none', 'readonly'):
                continue

            seq = detail['detail_seq']
            if seq not in grouped:
                grouped[seq] = []
            grouped[seq].append(detail)

        return grouped

    @staticmethod
    def delete_by_application(application_id):
        """
        申請IDに紐づく申請詳細データを全て削除

        Args:
            application_id: 申請ID

        Returns:
            int: 削除した件数
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            DELETE FROM T_APPLICATION_DETAIL
            WHERE application_id = :application_id
        """

        cursor.execute(sql, {'application_id': application_id})
        conn.commit()

        rows_deleted = cursor.rowcount
        cursor.close()

        return rows_deleted
