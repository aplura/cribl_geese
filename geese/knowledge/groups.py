import json
import os
from deepdiff import DeepDiff
from geese.knowledge.base import BaseKnowledge


class Groups(BaseKnowledge):
    def __init__(self, leader, args=None, logger=None, group=None, fleet=None, product="stream", **kwargs):
        super().__init__(leader, args, logger, **kwargs)
        self.obj_type = "groups"
        self.default_types = []
        self.endpoint = f"products/{product}/groups" if f'{leader["is_cloud"]}' == "true" else f"master/groups"
        self.group = None
        self.supports_groups = False

    def export(self):
        action = f"export_{self.obj_type}"
        data = self.get(self.endpoint)
        if data.status_code == 200 and data.json():
            items = [p for p in data.json()["items"] if p["id"] not in self.default_types or self.args.keep_defaults]
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

    def update(self, item=None):
        if item is None:
            item = {}
        action = f"import_{self.obj_type}"
        changes = {"id": item["id"] if "id" in item else "Unknown",
                   "previous": {"status": "not_updated", "data": {}},
                   "updated": {"status": "not_updated", "data": {}}}
        try:
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
                changes["previous"] = {"status": "error", "result": result}
            result = self.post(self.endpoint, payload=item)
            if result.status_code != 200:
                self._log("info", action=action, item_type=self.obj_type, item_id=item["id"],
                          destination=self.url, message="Could not Create",
                          conflict_resolution=self.args.conflict_resolve)
                if result.text.find("already exist") != -1 and self.args.conflict_resolve == "update":
                    result = self.patch(self._endpoint_by_id(item_id=item["id"]), payload=item)
                    if result.status_code != 200:
                        self._display(f"\t{item['id']}: Update failed. {result.text}", self.colors.get("error"))
                        changes["updated"] = {"status": "update_failed", "data": item, "error": result.text}
                    else:
                        self._display(f"\t{item['id']}: Update successful.", self.colors.get("success", "green"))
                        changes['updated'] = {"status": "success", "data": item}
                elif result.text.find("should have required property") != -1:
                    msg = result.text
                    try:
                        msg = result.json()["message"]
                        msg = json.loads(msg)
                        t = []
                        for m in msg:
                            t.append(f'{m["keyword"]}:\n\t\t{m["message"]}\n\t\t{m["params"]}\n\t\t{m["schemaPath"]}')
                        msg = "\n\t".join(t)
                    except Exception as e:
                        msg = result.text
                    self._display(f"\t{item['id']}: Create failed. \n\t{msg}", self.colors.get("error", "red"))
                    changes["updated"] = {"status": "create_failed", "data": item, "error": result.text}
                elif self.args.conflict_resolve == "ignore":
                    self._display(f"\t{item['id']}: Ignoring conflict/error.", self.colors.get("success", "green"))
                    changes["updated"] = {"status": "ignored", "data": item}
                else:
                    # some other error
                    self._display(f"\t{item['id']}: Error while trying to create. {result.text}",
                                  self.colors.get("error"))
                    changes["updated"] = {"status": "update_failed", "data": item, "error": result}
            else:
                self._display(f"\t{item['id']}: Update succeeded.", self.colors.get("success", "green"))
                changes['updated'] = {"status": "success", "data": item}
                changes["diff"] = json.loads(
                    DeepDiff(changes["previous"]["data"], changes["updated"]["data"]).to_json())
            return changes
        except Exception as e:
            self._display_error("Unhandled Exception", e)
            changes["diff"] = json.loads(
                DeepDiff(changes["previous"]["data"], changes["updated"]["data"]).to_json())
            return changes

    def simulate(self, item=None):
        if item is None:
            item = {}
        action = f"import_{self.obj_type}"
        changes = {"id": item["id"] if "id" in item else "Unknown",
                   "previous": {"status": "does_not_exist", "data": {}},
                   "current": {"status": "import_data", "data": item}}
        try:
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

    def list_all(self):
        gs = self.export()
        for group in gs:
            group["workers"] = self.workers(group=group)
        return gs

    def workers(self, group=None):
        # /api/v1/master/workers?filterExp=info.cribl.distMode%3D%3D%22worker%22&&group=="aws-prd-global-hec"
        action = f"export_{self.obj_type}_workers"
        payload = {
            "filterExp": f'group=="{group}"'
        }
        data = self.get(endpoint=f"master/workers", payload=payload)
        if data.status_code == 200 and data.json():
            items = [p for p in data.json()["items"] if p["id"] not in self.default_types or self.args.keep_defaults]
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
