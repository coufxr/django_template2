import logging

import jwt
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("django")


class Apple:
    @classmethod
    def verify(cls, access_token):
        conf = settings.APPLEr

        client_id, client_secret = cls.get_key_and_secret()

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": access_token,
            "grant_type": "authorization_code",
        }

        res = requests.post(conf["ACCESS_TOKEN_URL"], data=data, headers=headers)
        response_dict = res.json()
        logger.info(f"apple auth: {response_dict}")
        id_token = response_dict.get("id_token", None)

        response_data = {}
        if id_token:
            decoded = jwt.decode(id_token, "", verify=False)
            (response_data.update({"email": decoded["email"]}) if "email" in decoded else None)
            (response_data.update({"uid": decoded["sub"]}) if "sub" in decoded else None)

        return True, response_data

    @staticmethod
    def get_key_and_secret():
        conf = settings.APPLE
        headers = {"kid": conf["KEY_ID"]}

        payload = {
            "iss": conf["TEAM_ID"],
            "iat": timezone.now(),
            "exp": timezone.now() + conf["EXP"],
            "aud": "https://appleid.apple.com",
            "sub": conf["CLIENT_ID"],
        }

        client_secret = jwt.encode(payload, conf["PRIVATE_KEY"], algorithm="ES256", headers=headers).decode("utf-8")

        return settings.CLIENT_ID, client_secret
