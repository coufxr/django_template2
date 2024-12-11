import logging
import time

from rest_framework.response import Response

logger = logging.getLogger("django")


class APIException(Exception):
    def __init__(self, msg="非法请求", code=40000, status=400):
        self.msg = msg
        self.code = code
        self.status = status


class JSONResponse(Response):
    def __init__(
        self,
        data=None,
        code=0,
        msg="",
        status=None,
        template_name=None,
        headers=None,
        exception=False,
        content_type=None,
    ):
        super().__init__(data, status, template_name, headers, exception, content_type)

        self.data = {
            "data": data,
            "msg": msg,
            "code": code,
            "ts": int(time.time() * 1000),
        }


def logging_print(func):
    def wrapped(exc, context):
        response = func(exc, context)
        if response.status_code != 200 and response.status_code != 500:
            logger.info(
                f"request_response_info: {context['view'].request.query_params},"
                f"{context['view'].request.data}, {response.data}"
            )
        return response

    return wrapped


class DynamicSerializerMixin:
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
