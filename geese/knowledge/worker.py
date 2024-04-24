import json
import os
from deepdiff import DeepDiff
from geese.knowledge.base import BaseKnowledge


class Worker(BaseKnowledge):
    def __init__(self, leader, args=None, logger=None, group=None, fleet=None, product="stream", **kwargs):
        super().__init__(leader, args, logger, **kwargs)
        self.obj_type = "worker"
        self.default_types = []
        self.endpoint = None
        self.id = kwargs["id"] if "id" in kwargs else None
        self.group = fleet if fleet is not None else group
        self.mode = "managed-edge" if fleet is not None else "worker"
        if "info" in kwargs and "cribl" in kwargs["info"]:
            self.mode = kwargs["info"]["cribl"]["distMode"]

    def migrate_leader(self, group=None, leader=None, auto_restart=True):
        payload = {
            "mode": self.mode,
            "group": group,
            "envRegex": "/^CRIBL_/",
            "master": {
                "loadBalanced": True,
                "compression": "none",
                "tls": {
                    "disabled": False,
                    "rejectUnauthorized": False,
                    "servername": leader["url"].replace("https://", "")
                },
                "connectionTimeout": 10000,
                "writeTimeout": 60000,
                "tokenTTLMinutes": 60,
                "port": 4200,
                "host": leader["url"].replace("https://", ""),
                "proxy": {
                    "disabled": True
                },
                "authToken": str(leader["token"]),
                "resiliency": "none"
            },
            "id": "distributed"
        }
        endpoint = f'w/{self.id}/system/instance/distributed'
        results = self.patch(endpoint, payload=payload)
        if results.status_code == 200:
            self._display(f"\tWorker {self.id}: migrated successfully to {leader['url']}", self.colors.get("success", "green"))
            if auto_restart:
                return self.restart()
        else:
            self._display(f"\tWorker {self.id}: migration failed. {results.status_code}: {results.text}", self.colors.get("error", "red"))
            return False
        return True

    def restart(self):
        shutdown_resp = self.post(f'w/{self.id}/system/settings/restart')
        if shutdown_resp.status_code == 200:
            self._display(f'\tWorker {self.id}: Restart success.', self.colors.get("success", "green"))
            return True
        else:
            self._display(f'\tWorker {self.id}: Restart failure. {shutdown_resp.status_code}: {shutdown_resp.text}', self.colors.get("error", "green"))
            return False
