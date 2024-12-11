# 手机号正则表达式
PHONE_REGEX = r"^(13[0-9]|14[01456879]|15[0-35-9]|16[2567]|17[0-9]|18[0-9]|19[0-35-9])\d{8}$"


# 小程序 access_token
CM_WECHAT_MP_ACCESS_TOKEN = "wechat_mp:access_token"


class Code:
    # 400
    RATE_LIMIT_400 = 40041  # 限制请求频率

    # 401
    INVALID_TOKEN_401 = 40141  # 无效 token
