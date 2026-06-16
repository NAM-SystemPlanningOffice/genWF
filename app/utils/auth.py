"""
認証モジュール

環境に応じた認証方式でユーザーIDを取得：
- 開発環境: フォーム入力（手動ログイン）
- staging/production環境: Entra ID Easy Auth (Azure App Service)
"""
import os


def get_authenticated_user_from_request(request):
    """
    リクエストから認証済みユーザーIDを取得

    環境に応じて適切な方法でユーザーIDを取得：
    - 開発環境: フォーム入力（auth.pyで処理）
    - staging/production: Entra ID Easy Auth (X-MS-CLIENT-PRINCIPAL-NAME)

    Args:
        request: Flaskのrequestオブジェクト

    Returns:
        str: ユーザーID（ドメイン名を除いたUsername）
             取得できない場合は None
    """
    # 環境判定: DEPLOYMENT_SLOTで判断
    deployment_slot = os.environ.get('DEPLOYMENT_SLOT', 'development')

    if deployment_slot == 'development':
        # 開発環境: フォーム入力（auth.pyで処理）
        return None

    else:
        # staging/production環境: Entra ID Easy Auth
        # X-MS-CLIENT-PRINCIPAL-NAME からユーザーID取得
        principal_name = request.headers.get('X-MS-CLIENT-PRINCIPAL-NAME')

        if principal_name:
            # user@domain.com → user に変換
            if '@' in principal_name:
                user_id = principal_name.split('@')[0]
            else:
                user_id = principal_name

            return user_id

        # Easy Authが有効でない場合（エラー状態）
        return None
