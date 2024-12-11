import logging

from django.conf import settings
from django.contrib.auth.backends import BaseBackend, get_user_model

from apps.account.consts import LoginType
from apps.account.models import AppleAccount, WeChatAccount
from helper.sms import SMSService
from django_template.drf import APIException
from helper.apple import Apple
from helper.we_chat import WeChat, WeChatMP
from utils.crypt import Crypt

logger = logging.getLogger("django")

UserModel = get_user_model()


class PhoneModelBackend(BaseBackend):
    def authenticate(self, request, phone="", captcha="", **kwargs):
        if kwargs["type"] != LoginType.PHONE:
            return

        if not phone and not captcha:
            return

        if phone not in settings.CHECK_PHONE:
            ok, msg = SMSService.verify_code(phone, captcha)
            if not ok:
                raise APIException(msg)
        else:
            logger.warning("authenticate: check user login")

        try:
            user = UserModel.objects.get(phone=phone)
        except UserModel.DoesNotExist:
            user = UserModel(phone=phone, source=LoginType.PHONE)
            user.save()

        return user


class WeChatModelBackend(BaseBackend):
    def authenticate(self, request=None, code=None, **kwargs):
        if kwargs["type"] != LoginType.WE_CHAT:
            return

        if not code:
            return

        ok, payload, access_token = WeChat.get_access_token(code)
        logger.info(f"wechat auth: {payload}")
        if not ok:
            logger.info(f"wechat auth failed: {payload}")
            raise APIException("认证失败", status=401, code=40199)

        access_token = payload["access_token"]
        openid = payload["openid"]

        ok, payload2 = WeChat.get_user_info(access_token, openid)
        logger.info(f"wechat auth: {payload2}")
        if ok:
            logger.info(f"wechat auth failed: {payload2}")
            raise APIException("认证失败", status=401, code=40199)

        wechat_account = WeChatAccount.objects.filter(openid=openid).first()
        if wechat_account:
            account_id = wechat_account.account_id
            account = UserModel.objects.get(id=account_id)
        else:
            account = UserModel(source=LoginType.WE_CHAT)
            account.save()

            WeChatAccount.objects.bulk_create(
                [
                    WeChatAccount(
                        account_id=account.id,
                        openid=openid,
                        nickname=payload2["nickname"],
                        sex=payload2["sex"],
                        province=payload2["province"],
                        city=payload2["city"],
                        country=payload2["country"],
                        head_image_url=payload2["headimageurl"],
                        union_id=payload2["unionid"],
                    )
                ]
            )
        return account


class AppleModelBackend(BaseBackend):
    def authenticate(self, request=None, access_token=None, **kwargs):
        if kwargs["type"] != LoginType.APPLE:
            return

        if not access_token:
            return

        ok, payload = Apple.verify(access_token)
        logger.info(f"apple auth: {payload}")
        if not ok:
            logger.info(f"apple auth failed: {payload}")
            raise APIException("认证失败", status=401, code=40199)

        uid = payload["uid"]
        email = payload["email"]

        apple_account = AppleAccount.objects.filter(uid=uid).first()
        if apple_account:
            account_id = apple_account.account_id
            account = UserModel.objects.get(id=account_id)
        else:
            account = UserModel(source=LoginType.APPLE)
            account.save()

            AppleAccount.objects.bulk_create([AppleAccount(account_id=account.id, uid=uid, email=email)])
        return account


class WeChatMPModelBackend(BaseBackend):
    @staticmethod
    def get_phone(session_key, encrypted_data, iv):
        # 解密手机号
        conf = settings.WE_CHAT

        try:
            c = Crypt(conf["appid"], session_key)
            payload = c.decrypt(encrypted_data, iv)
        except:  # noqa
            logger.info("wechat: decrypt failed", exc_info=True)
            raise APIException("认证失败", status=401, code=40199)

        if not (payload["countryCode"] == "86" and payload["purePhoneNumber"]):
            logger.info(f"wechat: not a valid phone {payload}")
            raise APIException("认证失败", status=401, code=40199)

        return payload["purePhoneNumber"]

    def authenticate(self, request=None, code=None, iv=None, encrypted_data=None, **kwargs):
        """
        微信小程序登录
        """
        if kwargs["type"] != LoginType.WE_CHAT_MP:
            return

        if not (code and iv and encrypted_data):
            return

        ok, payload = WeChatMP.jsoncode2session(code)
        logger.info(f"wechat auth: {payload}")
        if not ok:
            logger.info(f"wechat auth failed: {payload}")
            raise APIException("认证失败", status=401, code=40199)

        session_key = payload["session_key"]
        openid = payload["openid"]

        phone = self.get_phone(session_key, encrypted_data, iv)

        wechat_account = WeChatAccount.objects.filter(openid=openid).first()

        # 按手机号查
        account = UserModel.objects.filter(phone=phone).first()
        if not account:
            account = UserModel(source=LoginType.WE_CHAT_MP, phone=phone)
            account.save()

        if wechat_account:
            wechat_account.session_key = session_key
            wechat_account.account_id = account.id
            wechat_account.save(update_fields=["session_key", "account_id"])
        else:
            WeChatAccount.objects.bulk_create(
                [WeChatAccount(account_id=account.id, openid=openid, session_key=session_key)],
                ignore_conflicts=True,
            )
        return account
