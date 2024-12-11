import logging
import hashlib

import requests
from django.conf import settings

from django_template import consts
from utils.redisx import cache_fn

logger = logging.getLogger("django")


class SHA1:
    @staticmethod
    def get_SHA1(token, timestamp, nonce, encrypted_msg):
        s = "".join(sorted([token, timestamp, nonce, encrypted_msg]))
        return hashlib.sha1(s.encode("utf-8")).hexdigest()


class WeChat:
    @classmethod
    def get_access_token(cls, code):
        conf = settings.WE_CHAT
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "appid": conf["appid"],
            "secret": conf["secret"],
        }
        url = f'{conf["domain"]}/sns/oauth2/access_token'
        resp = requests.get(url, params=params)
        resp_json = resp.json()
        if "access_token" not in resp_json:
            return False, resp_json
        return True, resp_json

    @staticmethod
    def get_user_info(access_token, openid):
        conf = settings.WE_CHAT
        params = {"access_token": access_token, "openid": openid}
        url = f'{conf["domain"]}/sns/userinfo'
        resp = requests.get(url, params=params)
        resp_json = resp.json()
        if "openid" not in resp_json:
            return False, resp_json
        return True, resp_json

    @staticmethod
    def check_signature(signature, timestamp, nonce, encrypted_msg=""):
        conf = settings.WE_CHAT
        _signature = SHA1.get_SHA1(conf["token"], timestamp, nonce, encrypted_msg)
        return _signature == signature


class WeChatMP:
    """
    微信小程序

    """

    @classmethod
    def jsoncode2session(cls, code):
        """
        code 换取 token

        https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-login/code2Session.html

        """
        conf = settings.WE_CHAT
        params = {
            "grant_type": "authorization_code",
            "js_code": code,
            "appid": conf["appid"],
            "secret": conf["secret"],
        }
        url = f'{conf["domain"]}/sns/jscode2session'
        resp = requests.get(url, params=params)
        resp_json = resp.json()
        if "errcode" in resp_json:
            return False, resp_json
        return True, resp_json

    @staticmethod
    @cache_fn(key=consts.CM_WECHAT_MP_ACCESS_TOKEN, timeout=7000)
    def get_access_token():
        """
        获取接口调用凭证

        https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/mp-access-token/getAccessToken.html

        """
        conf = settings.WE_CHAT
        params = {
            "grant_type": "client_credential",
            "appid": conf["appid"],
            "secret": conf["secret"],
        }

        url = f'{conf["domain"]}/cgi-bin/token'
        resp = requests.get(url, params=params)
        resp_json = resp.json()
        if "errcode" in resp_json:
            logger.error(f"wechat_mp:get_access_token: failed {resp_json}")
            return ""
        return resp_json["access_token"]

    @staticmethod
    def get_user_phone_number(code, access_token):
        """
        获取手机号

        https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-info/phone-number/getPhoneNumber.html

        """
        conf = settings.WE_CHAT
        params = {"access_token": access_token, "code": code}
        json_ = {"code": code}
        url = f'{conf["domain"]}/wxa/business/getuserphonenumber'
        resp = requests.post(url, params=params, json=json_)
        resp_json = resp.json()
        if "errcode" in resp_json and resp_json["errcode"] != 0:
            return False, resp_json
        return True, resp_json

    @staticmethod
    def get_miniprogram_state():
        if settings.ENVIRONMENT == "prod":
            return "formal"
        else:
            return "developer"

    @classmethod
    def subscribe(cls, openid, template_id, path=None, **kwargs):
        """
        下发订阅消息

        https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/mp-message-management/subscribe-message/sendMessage.html

        """
        conf = settings.WE_CHAT
        params = {"access_token": cls.get_access_token()}
        json_ = {
            "template_id": template_id,
            "touser": openid,
            "data": {k: {"value": v} for k, v in kwargs.items()},
            "miniprogram_state": cls.get_miniprogram_state(),
            "lang": "zh_CN",
        }
        if path:
            json_["page"] = path
        url = f'{conf["domain"]}/cgi-bin/message/subscribe/send'
        resp = requests.post(url, params=params, json=json_)
        resp_json = resp.json()
        if "errcode" in resp_json and resp_json["errcode"] != 0:
            return False, resp_json
        return True, resp_json
