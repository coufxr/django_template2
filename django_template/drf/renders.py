import logging

from rest_framework.renderers import JSONRenderer as DRFJSONRenderer

from django_template.drf import JSONResponse

logger = logging.getLogger("django")


class JSONRenderer(DRFJSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            resp = JSONResponse()
            data = resp.data
        elif not ("code" in data and "msg" in data and "data" in data):
            if isinstance(data, list):
                resp = JSONResponse({"items": data})
                data = resp.data
            elif isinstance(data, dict):
                resp = JSONResponse(data)
                data = resp.data
        code = data.get("code", 0)
        if (code == 0 and renderer_context["response"].status_code != 200) or (
            code != 0 and renderer_context["response"].status_code == 200
        ):
            logger.info(f"{renderer_context['request']} " f"{renderer_context['response'].data}")

        return super().render(data, accepted_media_type, renderer_context)
