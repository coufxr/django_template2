# 限制频率
# 发送短信
RL_VERIFY_CODE_HOUR = "verify_code:hour:%s"
RL_VERIFY_CODE_DAY = "verify_code:day:%s:%s"


# 登录方式
class LoginType:
    PHONE = 1  # 手机号登录
    WE_CHAT = 2  # 微信登录 iOS/Android
    APPLE = 3  # 苹果登录
    WE_CHAT_MP = 4  # 微信小程序登录

    @classmethod
    def values(cls):
        return [cls.PHONE, cls.WE_CHAT, cls.APPLE, cls.WE_CHAT_MP]


class ShopConfirmStatus:
    CHECKING = 10  # 审核中
    REJECTED = 20  # 已驳回
    APPROVED = 30  # 审核通过
