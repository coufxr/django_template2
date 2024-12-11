from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
)


class JWTAuthenticationOrNot(JWTAuthentication):
    """
    存在有效 token 则解析，不存在也不报错

    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except InvalidToken:
            return None

    def get_user(self, validated_token):
        """
        注销 用户和token 后 报错,
        在此捕捉 使其不报 401
        """
        try:
            return super().get_user(validated_token)
        except AuthenticationFailed:
            return None
