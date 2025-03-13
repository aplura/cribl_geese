import json
from deepdiff import DeepDiff
from geese.knowledge.base import BaseKnowledge


class Routes(BaseKnowledge):
    obj_type = "routes"

    def __init__(self, leader, args=None, logger=None, group=None, fleet=None, **kwargs):
        super().__init__(leader, args, logger, **kwargs)
        self.default_types = []
        self.endpoint = "routes/default"
        self.api_path = f"/{self.endpoint}"
        self.group = None
        if (group is not None or fleet is not None) and not self._is_free:
            self.group = fleet if fleet is not None else group
            self.is_fleet = True if fleet is not None else False
            self.endpoint = f"m/{self.group}/routes/default"

    def export(self):
        action = f"export_{self.obj_type}"
        data = self.get(self.endpoint)
        if data.status_code == 200 and data.json():
            items = [p for p in data.json()["items"] if
                     (not ("conf" in p and "pack" in p["conf"]) and p[
                         "id"] not in self.default_types) or self.args.keep_defaults]
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
        # CHANGE THIS TO BE NON-DESTRUCTIVE (don't overwrite IDs that we don't know about.)
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
            new_routes = result[0]
            existing_routes = []
            added_routes = []
            self._log("debug", action="updating_routes", existing_routes=new_routes)
            changes["previous"]["data"] = {"routes": new_routes}
            if len(result) > 0:
                for r in new_routes.get("routes", []):
                    self._log("debug", action="updating_routes", step="adding_id_to_existing",id=r["id"])
                    existing_routes.append(r["id"])
            else:
                changes["previous"] = {"status": "error", "result": result}
            for val in item.get("routes", []):
                self._log("debug", action="updating_routes", step="checking_route",id=val["id"])
                if val["id"] in existing_routes:
                    idx = existing_routes.index(val["id"])
                    self._display(f"\t\t\tFound route '{val['id']}' at index '{idx}': replacing", color="blue")
                    new_routes["routes"][idx] = val
                else:
                    self._log("debug", action="updating_routes", step="pre-pending-route",id=val["id"])
                    new_routes["routes"].insert(0, val)
                    existing_routes.insert(0, val["id"])
                    added_routes.append(val["id"])
            # print(existing_routes, [x["id"] for x in new_routes.get("routes",[])], added_routes )
            result = self.patch(self.endpoint, payload=new_routes)
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
                    except:
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
                changes['updated'] = {"status": "success", "data": new_routes}
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

    def add(self, item=None):
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
            existing_routes = [r["id"] for r in result[0]["routes"]]
            if item["id"] not in existing_routes:
                result[0]["routes"].insert(0, item)
            else:
                # If it exists, we don't want to overwrite "admin set" settings. Only filter and description and pipeline.
                e_id = existing_routes.index(item["id"])
                result[0]["routes"][e_id]["description"] = item["description"]
                result[0]["routes"][e_id]["filter"] = item["filter"]
                result[0]["routes"][e_id]["pipeline"] = item["pipeline"]
            response = self.patch(self.endpoint, payload=result[0])
            if response.status_code != 200:
                self._log("info", action=action, item_type=self.obj_type, item_id=item["id"],
                          destination=self.url, message="Could not Create",
                          conflict_resolution=self.args.conflict_resolve)
                if response.text.find("already exist") != -1 and self.args.conflict_resolve == "update":
                    response = self.patch(self._endpoint_by_id(item_id=item["id"]), payload=item)
                    if response.status_code != 200:
                        self._display(f"\t{item['id']}: Update failed. {response.text}", self.colors.get("error"))
                        changes["updated"] = {"status": "update_failed", "data": item, "error": response.text}
                    else:
                        self._display(f"\t{item['id']}: Update successful.", self.colors.get("success", "green"))
                        changes['updated'] = {"status": "success", "data": item}
                elif response.text.find("should have required property") != -1:
                    msg = response.text
                    try:
                        msg = response.json()["message"]
                        msg = json.loads(msg)
                        t = []
                        for m in msg:
                            t.append(f'{m["keyword"]}:\n\t\t{m["message"]}\n\t\t{m["params"]}\n\t\t{m["schemaPath"]}')
                        msg = "\n\t".join(t)
                    except:
                        msg = response.text
                    self._display(f"\t{item['id']}: Create failed. \n\t{msg}", self.colors.get("error", "red"))
                    changes["updated"] = {"status": "create_failed", "data": item, "error": response.text}
                elif self.args.conflict_resolve == "ignore":
                    self._display(f"\t{item['id']}: Ignoring conflict/error.", self.colors.get("success", "green"))
                    changes["updated"] = {"status": "ignored", "data": item}
                else:
                    # some other error
                    self._display(f"\t{item['id']}: Error while trying to create. {response.text}",
                                  self.colors.get("error"))
                    changes["updated"] = {"status": "update_failed", "data": item, "error": response}
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
