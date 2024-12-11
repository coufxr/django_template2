import logging

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework_simplejwt import exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings

from apps.account import consts
from django_template import consts as g_consts
from django_template.drf import DynamicSerializerMixin

logger = logging.getLogger("django")


class CaptchaSerializer(serializers.Serializer):
    phone = serializers.RegexField(g_consts.PHONE_REGEX, error_messages={"invalid": "输入有效的手机号码"})


class AuthTokenObtainPairSerializer(DynamicSerializerMixin, TokenObtainPairSerializer):
    captcha = serializers.CharField(
        max_length=4,
        min_length=4,
        error_messages={
            "max_length": "验证码长度限制4位",
            "min_length": "验证码长度限制4位",
            "required": "请输入验证码",
        },
    )  # 验证码登录
    phone = serializers.RegexField(g_consts.PHONE_REGEX, error_messages={"invalid": "输入有效的手机号码"})
    type = serializers.ChoiceField(choices=consts.LoginType.values(), default=consts.LoginType.PHONE)
    code = serializers.CharField()
    iv = serializers.CharField()
    encrypted_data = serializers.CharField()
    access_token = serializers.CharField()

    def validate(self, attrs):
        self._authenticate(attrs)

        refresh = self.get_token(self.user)

        token = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        logger.info(f"login {token=} {refresh=}")

        data = {"token": token, "phone": self.user.phone}
        logger.info(f"login resp: {data}")

        return data

    def _authenticate(self, attrs):
        authenticate_kwargs = {k: v for k, v in attrs.items()}
        logger.info(f"login params: {authenticate_kwargs}")
        try:
            authenticate_kwargs["request"] = self.context["request"]
        except KeyError:
            pass

        self.user = authenticate(**authenticate_kwargs)

        if not api_settings.USER_AUTHENTICATION_RULE(self.user):
            logger.error("login fail")
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        return {}


class AccountSerializer(serializers.Serializer):
    captcha = serializers.CharField(
        max_length=4,
        min_length=4,
        error_messages={
            "max_length": "验证码长度限制4位",
            "min_length": "验证码长度限制4位",
            "required": "请输入验证码",
        },
        required=False,
    )  # 验证码登录


class AccountInfoSerializer(serializers.Serializer):
    nickname = serializers.CharField(allow_blank=True, required=False)
    avatar = serializers.CharField(allow_blank=True, required=False)
    name = serializers.CharField(allow_blank=True, required=False)
    sex = serializers.CharField(allow_blank=True, required=False)
    industry = serializers.ListField(
        child=serializers.CharField(),
        min_length=2,
        max_length=2,
        error_messages={
            "max_length": "长度限制2位",
            "min_length": "长度限制2位",
        },
        required=False,
    )
    region = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        max_length=3,
        error_messages={
            "max_length": "长度限制1位",
            "min_length": "长度限制1位",
        },
        required=False,
    )
    phone = serializers.IntegerField(read_only=True, required=False)
    mail = serializers.CharField(allow_blank=True, required=False)


class AccountPhoneSerializer(CaptchaSerializer, AccountSerializer):
    """"""
