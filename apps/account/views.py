from functools import partial

from django.conf import settings
from django.db import transaction
from django_template import consts as g_consts
from rest_framework import generics
from rest_framework.generics import RetrieveUpdateAPIView, UpdateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.account import consts, serializers
from apps.account.models import Account, AccountInfo
from django_template.drf import APIException, JSONResponse
from helper.sms import SMSService
from utils.redisx import RateLimitException


class CaptchaView(generics.GenericAPIView):
    serializer_class = serializers.CaptchaSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        phone = vd["phone"]
        if phone in settings.CHECK_PHONE:
            return JSONResponse()

        try:
            captcha = SMSService.gen_code(phone)
        except RateLimitException:
            raise APIException("操作过于频繁，请稍后再试", code=g_consts.Code.RATE_LIMIT_400)

        transaction.on_commit(lambda: SMSService.send_sms(phone, captcha))
        return JSONResponse()


class AccountTokenObtainPairView(TokenObtainPairView):
    authentication_classes = []
    permission_classes = []

    def get_serializer_class(self):
        data = self.request.data
        type_ = data.get("type")
        if type_ == consts.LoginType.WE_CHAT:
            return partial(serializers.AuthTokenObtainPairSerializer, fields=["type", "code"])
        elif type_ == consts.LoginType.APPLE:
            return partial(
                serializers.AuthTokenObtainPairSerializer,
                fields=["type", "access_token"],
            )
        elif type_ == consts.LoginType.WE_CHAT_MP:
            return partial(
                serializers.AuthTokenObtainPairSerializer,
                fields=["type", "code", "iv", "encrypted_data"],
            )
        else:
            return partial(
                serializers.AuthTokenObtainPairSerializer,
                fields=["type", "phone", "captcha"],
            )


class AccountLogoutView(generics.GenericAPIView):
    serializer_class = serializers.AccountSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # params = serializer.validated_data

        # captcha = params['captcha']
        user_id = request.user.id

        instance = Account.objects.get(pk=user_id)
        # phone = instance.phone
        # ok, resp = SMSService.verify_code(phone, captcha)
        # if not ok:
        #     raise APIException(resp)

        # 校验 是否可注销
        # is_deregister = UserUseCase.is_logout(user_id)
        # if not is_deregister:
        #     raise APIException(msg='暂时不可注销')

        # 删除账号
        instance.delete()
        return JSONResponse()


class AccountInfoView(RetrieveUpdateAPIView):
    serializer_class = serializers.AccountInfoSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        instance = Account.objects.get(id=user_id)

        return instance

    def get(self, request, *args, **kwargs):
        instance = self.get_queryset()
        acc_info = AccountInfo.objects.filter(account_id=instance.id).first()

        if acc_info:
            info = acc_info.info
        else:
            info = {
                "name": None,
                "sex": None,
                "industry": None,
                "region": None,
                "mail": None,
            }

        info.update(
            {
                "nickname": instance.nickname,
                "avatar": instance.avatar,
                "phone": instance.phone,
            }
        )

        return JSONResponse(info)

    @transaction.atomic
    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        nickname = params.get("nickname")
        avatar = params.get("avatar")

        instance = self.get_queryset()
        if nickname:
            instance.nickname = params.pop("nickname")
        if avatar:
            instance.avatar = params.pop("avatar")

        instance.save()

        acc_info = AccountInfo.objects.filter(account_id=instance.id).first()
        if acc_info:
            acc_info.info = params
            acc_info.save()
        else:
            if params.get("name"):
                params["account_name"] = params.pop("name")
            AccountInfo.objects.create(account_id=instance.id, **params)

        return JSONResponse()

    def partial_update(self, request, *args, **kwargs):
        # 禁用
        return JSONResponse()


class AccountPhoneView(UpdateAPIView):
    serializer_class = serializers.AccountPhoneSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        instance = Account.objects.get(id=user_id)

        return instance

    @transaction.atomic
    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        captcha = params["captcha"]
        new_phone = params["phone"]  # 新的手机号

        instance = self.get_queryset()
        ok, resp = SMSService.verify_code(new_phone, captcha)
        if not ok:
            raise APIException(resp)
        # 校验
        if instance.phone == new_phone:
            raise APIException("更改手机号不可与原手机号一致")

        qs = Account.objects.filter(phone=new_phone).exclude(id=instance.id)
        if qs.exists():
            raise APIException("该手机号已绑定其他账号")

        instance.phone = new_phone
        instance.save()

        return JSONResponse()

    def partial_update(self, request, *args, **kwargs):
        # 禁用
        return JSONResponse()
