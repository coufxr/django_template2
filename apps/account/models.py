from django.db import models

from apps.common import consts as common_consts
from django_template.drf.djangox import BasicModel, SDBasicModel
from utils.tools import md5


class VerifyCode(BasicModel):
    id = models.AutoField(primary_key=True)
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    used = models.IntegerField(default=0)
    expiration_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "verify_code"


class Account(SDBasicModel):
    id = models.AutoField(primary_key=True)
    phone = models.CharField(max_length=11)
    nickname = models.CharField(max_length=32)
    avatar = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    source = models.IntegerField()

    class Meta:
        managed = False
        db_table = "account"

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @staticmethod
    def get_username():
        return ""

    def set_token(self, raw_token):
        self.token = md5(raw_token)

    def check_token(self, raw_token):
        return self.token == md5(raw_token)

    @property
    def phone_mask(self):
        return "%s****%s" % (self.phone[:3], self.phone[7:])


class AccountInfo(SDBasicModel):
    id = models.AutoField(primary_key=True)
    account_id = models.IntegerField()
    account_name = models.CharField(max_length=32)
    sex = models.IntegerField(default=0)  # 1:男,2:女
    mail = models.CharField(max_length=128)
    _industry = models.CharField(max_length=32, db_column="industry")
    province_code = models.CharField(max_length=20)
    city_code = models.CharField(max_length=20)
    district_code = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = "account_info"

    @property
    def region(self):
        """地区code"""
        code = [self.province_code, self.city_code, self.district_code]
        # 兼容港澳台
        for c in code[:]:
            if c == "":
                code.remove("")
        return code

    @region.setter
    def region(self, value):
        if not value:
            return
        if len(value) == 1:
            # 兼容港澳台
            self.province_code = value[0]
            self.city_code = ""
            self.district_code = ""
            return
        p, c, d = value
        self.province_code = p
        self.city_code = c
        self.district_code = d

    @property
    def industry(self):
        return self._industry.split(",")

    @industry.setter
    def industry(self, value):
        self._industry = ",".join(value)

    @property
    def info(self):
        return {
            "name": self.account_name,
            "sex": self.sex,
            "industry": self.industry,
            "region": self.region,
            "mail": self.mail,
        }

    @info.setter
    def info(self, info):
        if info.get("name"):
            self.account_name = info["name"]
        if info.get("sex"):
            self.sex = info["sex"]
        if info.get("industry"):
            self.industry = info["industry"]
        if info.get("region"):
            self.region = info["region"]
        if info.get("mail"):
            self.mail = info["mail"]


class WeChatAccount(SDBasicModel):
    id = models.AutoField(primary_key=True)
    account_id = models.IntegerField()
    openid = models.CharField(max_length=100)
    session_key = models.CharField(max_length=255)

    # nickname = models.CharField(max_length=64)
    # sex = models.IntegerField(default=0)
    # province = models.CharField(max_length=25)
    # city = models.CharField(max_length=25)
    # country = models.CharField(max_length=25)
    # head_image_url = models.CharField(max_length=255)
    # union_id = models.CharField(max_length=100)

    class Meta:
        db_table = "wechat_account"


class AppleAccount(SDBasicModel):
    id = models.AutoField(primary_key=True)
    account_id = models.IntegerField()
    uid = models.CharField(max_length=64)
    email = models.CharField(max_length=255)

    class Meta:
        db_table = "apple_account"


class WeChatSubscribeTemplate(SDBasicModel):
    id = models.AutoField(primary_key=True)
    biz = models.CharField(max_length=255)
    wc_tpl_code = models.IntegerField()
    wc_tpl_id = models.CharField(max_length=255)
    path = models.CharField(max_length=255)

    class Meta:
        db_table = "wechat_subscribe_template"


class WeChatSubscribe(models.Model):
    id = models.AutoField(primary_key=True)
    biz = models.CharField(max_length=255)
    account_id = models.IntegerField()
    openid = models.CharField(max_length=100)
    wst_id = models.IntegerField()
    status = models.IntegerField(default=common_consts.WeChatSubscribeStatus.INIT)
    last_push_time = models.DateTimeField(blank=True, null=True)
    ext1 = models.IntegerField()

    class Meta:
        db_table = "wechat_subscribe"

    @classmethod
    def unsubscribe(cls, id_, account_id):
        return (
            cls.objects.filter(
                id=id_,
                status=common_consts.WeChatSubscribeStatus.INIT,
                account_id=account_id,
            ).update(status=common_consts.WeChatSubscribeStatus.CANCEL)
            > 0
        )

    @classmethod
    def get_subscribe(cls, account_id, biz, **kwargs):
        fn = getattr(cls, f"_get_{biz}_params")
        params = fn(**kwargs)
        inst = (
            cls.objects.filter(
                account_id=account_id,
                biz=biz,
                status=common_consts.WeChatSubscribeStatus.INIT,
                **params,
            )
            .order_by("-id")
            .first()
        )
        return inst.id if inst else 0

    @classmethod
    def _get_flow_params(cls, p_id, **kwargs):
        return {"ext1": p_id}

    @classmethod
    def _check_exists(cls, account_id, wst_id, **kwargs):
        return bool(
            cls.objects.filter(
                account_id=account_id,
                wst_id=wst_id,
                status=common_consts.WeChatSubscribeStatus.INIT,
                **kwargs,
            ).first()
        )

    @classmethod
    def check_flow_exists(cls, account_id, wst_id, p_id, **kwargs):
        return cls._check_exists(account_id, wst_id, ext1=p_id)
