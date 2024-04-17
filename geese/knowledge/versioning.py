import datetime
import json

from deepdiff import DeepDiff
from geese.knowledge.base import BaseKnowledge


class Versioning(BaseKnowledge):
    def __init__(self, leader, args=None, logger=None, group=None, fleet=None, **kwargs):
        super().__init__(leader, args, logger, **kwargs)
        self.obj_type = "versioning"
        self.default_types = []
        self.endpoint = "version/commit"
        self.group = None
        if group is not None or fleet is not None:
            self.group = fleet if fleet is not None else group
            self.endpoint = f"m/{self.group}/version/commit"

    def commit(self, message=None, deploy=False, effective=True):
        action = f"import_{self.obj_type}"
        changes = {"id": "versioning",
                   "previous": {"status": "not_updated", "data": {}},
                   "updated": {"status": "not_updated", "data": {}}}
        time_format = "%b %d, %Y %H:%M:%S"
        if message is None:
            message = f"{datetime.datetime.now().strftime(time_format)} UTC: No message"
        else:
            message = f"{datetime.datetime.now().strftime(time_format)} UTC: {message}"
        try:
            payload = {"message": message}
            if self.group is not None:
                payload["effective"] = effective
            self._log("info", action=action,
                      item_type=self.obj_type,
                      destination=self.url,
                      group=self.group)
            result = self.post(self.endpoint, payload=payload)
            if result.status_code != 200:
                self._log("info", action=action, item_type=self.obj_type,
                          destination=self.url, message="Could not commit", colors=self.colors)
                self._display(f"\tCommit: Error; {self.group}; {result.text}", self.colors.get("error", "red"))
                changes["updated"] = {"status": "update_failed", "data": payload, "error": result}
            else:
                r_json = result.json()
                version = r_json["items"][0]["commit"]
                self._display(f"\tCommit: Success; {self.group}; {version}", self.colors.get("success", "green"))
                if deploy and self.group is not None:
                    did_deploy, deploy_message = self.deploy(version)
                    self._log("debug", action="deploy", item_type=self.obj_type,
                              destination=self.url, message="Could not deploy", did_deploy=did_deploy, deploy_message=deploy_message)
                changes['updated'] = {"status": "success", "data": r_json}
                changes["diff"] = json.loads(
                    DeepDiff(changes["previous"]["data"], changes["updated"]["data"]).to_json())
            self._display("\tCommit Operation Complete")
            return changes
        except Exception as e:
            self._display_error("Unhandled Exception", e)
            changes["diff"] = json.loads(
                DeepDiff(changes["previous"]["data"], changes["updated"]["data"]).to_json())
            return changes

    def deploy(self, version=None):
        if self.group is None:
            return False, "No Group Specified"
        if version is None:
            return False, "Version Not Specified"
        endpoint = f"master/groups/{self.group}/deploy"
        action = "commit_deploy"
        changes = {"id": "versioning",
                   "previous": {"status": "not_updated", "data": {}},
                   "updated": {"status": "not_updated", "data": {}}}
        try:
            payload = {"version": version}
            self._log("info", action=action,
                      item_type=self.obj_type,
                      destination=self.url,
                      group=self.group)
            result = self.patch(endpoint=endpoint, payload=payload)
            if result.status_code != 200:
                self._log("info", action=action, item_type=self.obj_type,
                          destination=self.url, message="Could not deploy")
                self._display(f"\tDeploy: Error; {version}; {result.text}",
                              self.colors.get("error"))
                changes["updated"] = {"status": "update_failed", "data": payload, "error": result}
            else:
                self._display(f"\tDeploy: Success; {self.group}; {version}", self.colors.get("success", "green"))
                changes['updated'] = {"status": "success", "data": payload}
                changes["diff"] = json.loads(
                    DeepDiff(changes["previous"]["data"], changes["updated"]["data"]).to_json())
            return True, changes
        except Exception as e:
            self._display_error("Unhandled Exception", e)
            changes["diff"] = json.loads(
                DeepDiff(changes["previous"]["data"], changes["updated"]["data"]).to_json())
            return changes
