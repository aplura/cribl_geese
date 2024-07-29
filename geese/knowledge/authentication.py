import os

from geese.knowledge.base import BaseKnowledge


class Authentication(BaseKnowledge):
    obj_type = "authentication"

    def __init__(self, leader, args=None, logger=None, **kwargs):
        super().__init__(leader, args, logger, **kwargs)
        self.leader = leader
        self.headers = {"Content-type": "application/json"}

    def _get_auth_env(self, key):
        env_key = self.leader.get(key)
        if os.getenv(env_key):
            return os.getenv(env_key)
        return self.leader[key]

    def api_get_auth_data(self):
        try:

            username = self._get_auth_env("username")
            password = self._get_auth_env("password")
            payload = {"username": username,
                       "password": password}
            response = self.post("auth/login", payload=payload)
            print(f"{response}")
            if response.json() and "token" in response.json():
                return response.json()["token"], response.json()
            else:
                return None, response.json()
        except Exception as e:
            self._display_error("Unhandled api_get_auth_data Exception", e)

    def get_cloud_access_token(self):
        try:
            client_id = self._get_auth_env("client_id")
            client_secret = self._get_auth_env("client_secret")
            login_server = "https://login.cribl.cloud/oauth/token"
            audience = "https://api.cribl.cloud"
            if "cribl-staging.cloud" in self.url:
                login_server = "https://login.cribl-staging.cloud/oauth/token"
                audience = "https://api.cribl-staging.cloud"
            payload = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "audience": audience
            }
            self._log("debug", login_server=login_server, payload=payload)
            response = self.post(url=login_server, payload=payload)
            if response.status_code == 200 and "access_token" in response.json():
                return response.json()["access_token"], response.json()
            else:
                return None, response.json()
        except Exception as e:
            self._display_error("Unhandled get_cloud_access_token Exception", e)
