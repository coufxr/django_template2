import base64
import json
from Crypto.Cipher import AES


class Crypt:
    def __init__(self, appid, session_key):
        self.appid = appid
        self.session_key = session_key

    def decrypt(self, encrypted_data, iv):
        # base64 decode
        session_key = base64.b64decode(self.session_key)
        encrypted_data = base64.b64decode(encrypted_data)
        iv = base64.b64decode(iv)

        cipher = AES.new(session_key, AES.MODE_CBC, iv)

        decrypted = json.loads(self._unpad(cipher.decrypt(encrypted_data)).decode())

        if decrypted["watermark"]["appid"] != self.appid:
            raise Exception("Invalid Buffer")

        return decrypted

    @staticmethod
    def _unpad(s):
        return s[: -ord(s[len(s) - 1 :])]
