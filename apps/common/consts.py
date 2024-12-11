from enum import IntEnum


class WeChatSubscribeStatus(IntEnum):
    """
    微信消息订阅

    """

    INIT = 0  # 初始
    CANCEL = 10  # 取消
    FAILED = 21  # 推送失败
    PUSHED = 22  # 已推送
