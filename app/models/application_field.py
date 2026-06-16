"""
申請フィールドマスタモデル
"""
from app.utils.db import get_db_connection, dict_factory


class ApplicationField:
    """申請フィールドモデル"""

    @staticmethod
    def get_by_application_type(application_type_id):
        """
        申請種類IDからフィールド一覧を取得

        Args:
            application_type_id: 申請種類ID

        Returns:
            list: フィールドのリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                f.field_id,
                f.application_type_id,
                f.field_code,
                f.field_name,
                f.field_type,
                f.is_required_create,
                f.is_required_modify,
                f.is_required_delete,
                f.is_editable_modify,
                f.is_visible,
                f.is_key_field,
                f.pulldown_group_id,
                f.resource_column_name,
                f.resource_label_column,
                f.display_order,
                f.default_value,
                f.placeholder,
                f.help_text,
                p.group_code AS pulldown_group_code,
                p.is_dynamic AS pulldown_is_dynamic,
                p.dynamic_query AS pulldown_dynamic_query
            FROM M_APPLICATION_FIELD f
            LEFT JOIN M_PULLDOWN_GROUP p ON f.pulldown_group_id = p.pulldown_group_id
            WHERE f.application_type_id = :application_type_id
              AND f.is_active = 'Y'
            ORDER BY f.display_order, f.field_id
        """

        cursor.execute(sql, {'application_type_id': application_type_id})
        results = dict_factory(cursor)

        cursor.close()

        return results

    @staticmethod
    def get_pulldown_options(pulldown_group_id):
        """
        プルダウングループの選択肢を取得

        Args:
            pulldown_group_id: プルダウングループID

        Returns:
            list: 選択肢のリスト
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                option_id,
                pulldown_group_id,
                option_value,
                option_label,
                display_order,
                parent_option_id
            FROM M_PULLDOWN_OPTION
            WHERE pulldown_group_id = :pulldown_group_id
              AND is_active = 'Y'
            ORDER BY display_order, option_id
        """

        cursor.execute(sql, {'pulldown_group_id': pulldown_group_id})
        results = dict_factory(cursor)

        cursor.close()

        return results

    @staticmethod
    def get_dynamic_pulldown_options(dynamic_query, params=None):
        """
        動的プルダウンの選択肢を取得

        Args:
            dynamic_query: 動的取得SQL
            params: SQLパラメータ（dict）

        Returns:
            list: 選択肢のリスト（option_value, option_labelを含む）
        """
        import re
        conn = get_db_connection()
        cursor = conn.cursor()

        if params is None:
            params = {}

        # クエリ内で実際に使われているプレースホルダーを抽出
        placeholders = set(re.findall(r':(\w+)', dynamic_query))

        # 使われているパラメータのみをフィルタリング
        filtered_params = {k: v for k, v in params.items() if k in placeholders}

        from flask import current_app
        current_app.logger.info(f'[get_dynamic_pulldown] クエリ: {dynamic_query[:100]}...')
        current_app.logger.info(f'[get_dynamic_pulldown] 検出されたプレースホルダー: {placeholders}')
        current_app.logger.info(f'[get_dynamic_pulldown] 渡すパラメータ: {filtered_params}')

        cursor.execute(dynamic_query, filtered_params)
        results = dict_factory(cursor)

        current_app.logger.info(f'[get_dynamic_pulldown] 取得件数: {len(results)}件')

        cursor.close()

        return results
