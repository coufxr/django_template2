import logging
import random
import time
from datetime import datetime, timedelta

from django.conf import settings

from apps.account import consts
from apps.account.models import VerifyCode
from utils.redisx import RateLimit

logger = logging.getLogger("django")


class SMSService:
    @staticmethod
    def gen_code(phone):
        with (
            RateLimit(
                key=consts.RL_VERIFY_CODE_DAY % (time.strftime("%Y%m%d"), phone),
                limit=10,
                timeout=86400,
            ),
            RateLimit(key=consts.RL_VERIFY_CODE_HOUR % phone, limit=5, timeout=3600),
        ):
            code = random.randint(1000, 9999)
            VerifyCode.objects.create(
                phone=phone,
                code=code,
                expiration_time=datetime.now() + timedelta(seconds=300),
            )
            return str(code)

    @staticmethod
    def verify_code(phone, code):
        qs = VerifyCode.objects.filter(phone=phone, used=0).order_by("-id")[:1]
        if not qs:
            return False, "请先发送验证码"

        id_ = qs[0].id
        cnt = VerifyCode.objects.filter(id=id_, used=0, expiration_time__gte=datetime.now(), code=code).update(used=1)
        if cnt == 0:
            return False, "短信验证码错误"
        return True, ""

    @staticmethod
    def send_sms(phone, msg):
        sms_switch = settings.SMS_SWITCH
        if not sms_switch:
            logging.info(f"Message: sms will not send: {phone} {msg}")
            return

        Service.send_sms(phone, msg)
