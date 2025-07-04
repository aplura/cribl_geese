import json
from deepdiff import DeepDiff
from geese.knowledge.base import BaseKnowledge


class Groups(BaseKnowledge):
    obj_type = "groups"

    def __init__(self, leader, args=None, logger=None, group=None, fleet=None, product="stream", **kwargs):
        super().__init__(leader, args, logger, **kwargs)
        self.default_types = []
        self.group = group if group else fleet if fleet else "default"
        self.is_fleet = True if fleet is not None else False
        self.endpoint = f"products/{product}/groups" if f'{leader["is_cloud"]}' == "true" else f"master/groups"
        self.api_path = f"/{self.endpoint}"
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
        return self._update_item(action, item)

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
            group["workers"] = self.workers(group=group["id"])
        return gs

    def workers(self, group=None):
        # /api/v1/master/workers?filterExp=info.cribl.distMode%3D%3D%22worker%22&&group=="aws-prd-global-hec"
        action = f"export_{self.obj_type}_workers"
        payload = {
            "filterExp": f'group=="{group}" && info.cribl.distMode=="worker"',
        }
        data = self.get(endpoint="master/workers", payload=payload)
        if data.status_code == 200 and data.json():
            items = [p for p in data.json()["items"] if p["id"] not in self.default_types or self.args.keep_defaults
                     and p["group"] == group]
            self._log("info",
                      action=action,
                      source_url=self.url,
                      source_group=group,
                      count=len(items))
            return items
        else:
            self._log("warn", action=action,
                      source_url=self.url,
                      source_group=group,
                      count=0)
            return []
