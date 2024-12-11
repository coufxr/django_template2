import json
import logging

from rest_framework.views import (
    exception_handler as drf_exception_handler,
    set_rollback,
)

from django_template.drf import APIException, JSONResponse, logging_print

logger = logging.getLogger("django")


class BaseCode:
    # 500
    SERVER_ERROR = 50000  # 服务器错误


class BizCode(BaseCode):
    """
    公共业务错误码(0, 60-70)

    """

    # 400
    COMMON_ERROR = 40000  # 通用错误

    FIELD_ERROR = 40061  # 字段错误/缺失
    ADD_ERROR = 40062  # 添加错误
    UPDATE_ERROR = 40063  # 更新错误
    DELETE_ERROR = 40064  # 删除错误

    # 第三方服务-联通模块错误
    UNICOM_ERROR = 40101  # 联通错误


class DFCode(BaseCode):
    """
    框架错误码(80-99)

    """

    # 400
    DF_COMMON_ERROR = 40080  # 通用错误
    NOT_FOUND = 40081  # 未找到, NotFound
    # 401
    TOKEN_NOT_VALID = 40101  # token无效


@logging_print
def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        set_rollback()
        if isinstance(exc, APIException):
            return JSONResponse(code=exc.code, msg=exc.msg, status=exc.status)
        else:
            logger.error("err", exc_info=True)
            return JSONResponse(code=50000, msg="服务器错误", status=500)
    if response.status_code in (400, 404):
        set_rollback()
        return JSONResponse(code=40000, msg=json.dumps(response.data, ensure_ascii=False), status=400)
    elif response.status_code == 401:
        set_rollback()
        return JSONResponse(code=40100, msg=json.dumps(response.data, ensure_ascii=False), status=401)
    return response
