import json
from deepdiff import DeepDiff
from geese.knowledge.base import BaseKnowledge


class Secrets(BaseKnowledge):
    obj_type = "secrets"

    def __init__(self, leader, args=None, logger=None, group=None, fleet=None, **kwargs):
        super().__init__(leader, args, logger, **kwargs)
        try:
            self.default_types = []
            self.endpoint = "system/secrets"
            self.group = None
            if group is not None or fleet is not None:
                self.group = fleet if fleet is not None else group
                self.endpoint = "system/secrets"
        except Exception as e:
            self._display_error("Unhandled INIT Exception", e)

    def export(self):
        try:
            action = f"export_{self.obj_type}"
            data = self.get(self.endpoint)
            if data.status_code == 200 and data.json():
                items = data.json()["items"]
                self._log("info",
                          action=action,
                          source_url=self.url,
                          source_group=self.group,
                          count=len(items))
                return items
            else:
                self._log("warn", action=action,
                          source_url=self.url,
                          source_group=self.group,
                          count=0)
                return []
        except Exception as e:
            self._display_error(f"Unhandled EXPORT Exception: {self.obj_type}", e)
            return []

    def update(self, item=None):
        if item is None:
            item = {}
        action = f"import_{self.obj_type}"
        return self._update_item(action, item)

    def simulate(self, item=None):
        try:
            if item is None:
                item = {}
            action = f"import_{self.obj_type}"
            changes = {"id": item["id"] if "id" in item else "Unknown",
                       "previous": {"status": "does_not_exist", "data": {}},
                       "current": {"status": "import_data", "data": item}}
            self._log("info", action=action,
                      item_type=self.obj_type,
                      item_id=item["id"],
                      destination=self.url,
                      group=self.group)
            result = self.export()
            if len(result) > 0:
                for r in result:
                    if r["id"] == item["id"]:
                        changes["previous"] = {"status": "exists", "data": r}
            else:
                changes["previous"] = {"status": "error", "result": result, "data": {}}
            if changes["previous"]["status"] == "exists":
                changes["action"] = "will_update" if self.args.conflict_resolve == "update" else "will_ignore"
            else:
                changes["action"] = "will_create"
            changes["diff"] = json.loads(
                DeepDiff(changes["previous"]["data"], changes["current"]["data"]).to_json())
            return changes
        except Exception as e:
            self._display_error("Unhandled Exception", e)
            changes["diff"] = json.loads(
                DeepDiff(changes["previous"]["data"], changes["current"]["data"]).to_json())
            return changes
