import io
import logging
import os.path
import time
from pathlib import Path

import qiniu
from qiniu import Auth, put_data

logger = logging.getLogger("django")


class BaseUploader:
    def __init__(self, conf: dict[str, dict], *args, **kwargs):
        self.conf = conf

    def _upload(self, *args, **kwargs):
        raise NotImplementedError

    def upload_data(self, data, suffix):
        raise NotImplementedError

    def upload(self, data, filename: str):
        return self._upload(data, filename)

    def upload_file(self, filename: str):
        """
        上传文件
        :return:
        """
        with open(filename, "rb") as stream:
            return self._upload(stream.read(), filename)


class QiNiuUploader(BaseUploader):
    MIME_TYPE_MAPPING = {
        ".ppt": "application/vnd.ms-powerpoint",
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".pptx": "application/vnd.openxmlformats-officedocument" ".presentationml.presentation",
        ".txt": "text/plain",
    }

    def __init__(self, service="", *args, **kwargs):
        super().__init__(*args, **kwargs)

        conf = self.conf
        self._q = Auth(conf["access_key"], conf["secret_key"])

        svc_config = conf[service]
        self._bucket = svc_config["bucket"]
        self._token_timeout = svc_config["timeout"]
        self._domain = svc_config["domain"]

    def upload_data(self, data: bytes, suffix: str):
        with io.BytesIO(data) as stream:
            filename = f"{qiniu.utils.etag_stream(stream)}{suffix}"

        return self._upload(data, filename)

    def _upload(self, data, filename):
        """

        :param data:
        :param filename:
        :return:
        """
        if len(data) <= 0:
            logger.error("upload failed: empty data")
            return

        file_path = Path(filename)
        suffix = file_path.suffix

        archive = suffix.split(".")[-1]
        dir_path = f"{time.strftime('%Y%m')}/{archive}"

        key = f"{dir_path}/{filename}"

        # 生成上传 Token，可以指定过期时间等
        token = self._q.upload_token(self._bucket, key=key, expires=self._token_timeout)
        kwargs = {"mime_type": self.MIME_TYPE_MAPPING[suffix]}

        try:
            resp, info = put_data(token, key, data, **kwargs)
        except:
            logger.error("upload failed", exc_info=True)
            return

        if info.status_code != 200:
            logger.error(f"upload failed: {filename} to bucket {self._bucket}")
            return

        resp["download_url"] = f"{self._domain}/{resp['key']}"
        return resp
