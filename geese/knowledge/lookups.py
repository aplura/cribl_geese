import csv
import json
import os

from deepdiff import DeepDiff
from geese.knowledge.base import BaseKnowledge


class Lookups(BaseKnowledge):
    obj_type = "lookups"

    def __init__(self, leader, args=None, logger=None, group=None, fleet=None, **kwargs):
        super().__init__(leader, args, logger, **kwargs)
        try:
            self.default_types = []
            self.endpoint = "system/lookups"
            self.api_path = f"/{self.endpoint}"
            self.group = None
            if group is not None or fleet is not None:
                self.group = fleet if fleet is not None else group
            self.is_fleet = True if fleet is not None else False
            self.endpoint = "system/lookups"
        except Exception as e:
            self._display_error("Unhandled INIT Exception", e)

    def save_lookup_content(self, lookup_id, filename, save_to_directory="."):
        limit = 100000
        # TODO: Implement dynamic, config driven limits.
        response = self.get(f"{self.endpoint}/{lookup_id}/content?offset=0&limit={limit}")
        if response.status_code == 200:
            with open(os.path.join(save_to_directory, filename), "w", newline='') as lf:
                r = response.json()
                fieldnames = r["fields"]
                data = [fieldnames]
                [data.append(r) for r in r["items"]]
                writer = csv.writer(lf)
                writer.writerows(data)
        return response

    def export(self, save_file=True):
        try:
            action = f"export_{self.obj_type}"
            data = self.get(self.endpoint)
            items = []
            if data.status_code == 200 and data.json():
                for lookup in data.json()["items"]:
                    if save_file:
                        wg = self.group if self.group is not None else "default"
                        filename = f"{lookup['id']}"
                        if self.args.use_namespace:
                            filename = f"{lookup['id']}"
                        self._display(f"\tDownloading Lookup: {filename}", self.colors.get("info", "blue"))
                        # if self.args.split and self.args.use_namespace:
                        lookup_directory = self._gen_save_dir(self.args.directory, "lookups")
                        response = self.save_lookup_content(lookup['id'], filename, f"{lookup_directory}")
                        if response.status_code == 200:
                            self._display(f"\t{lookup['id']}: File downloaded.", self.colors.get("success", "green"))
                            lookup["local_location"] = lookup_directory
                            lookup["local_filename"] = filename
                        else:
                            self._display(f"\t{lookup['id']}: Error while trying to download. {response.text}",
                                          self.colors.get("error"))
                    items.append(lookup)
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

    def _upload_lookup_file(self, item):
        local_file = os.path.join(item["local_location"], item["id"])
        response = self.put(f"{self.endpoint}?filename={item['id']}", data=open(local_file, "rb"))
        if response.status_code == 200:
            self._display(f"\t{item['id']}: upload successful", self.colors.get("success", "green"))
            filename = None
            if "filename" in response.json():
                filename = response.json()["filename"]
            return {
                "id": item["id"],
                "fileInfo": {
                    "filename": filename
                }
            }
        else:
            self._display(f"\t{item['id']}: upload failed. Status: {response.status_code}", self.colors.get("error", "red"))
            return None

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
            if "local_location" in item:
                for r in self.export(save_file=False):
                    if r["id"] == item["id"]:
                        changes["previous"] = {"status": "exists", "data": r}
                    else:
                        changes["previous"] = {"status": "error", "status_code": "ID Not Found", "data": item}
                        config = self._upload_lookup_file(item)
                        if config is not None:
                            self._display(f"\t{item['id']}: Creating Lookup", self.colors.get("info", "green"))
                            response = self.post(self.endpoint, payload=config)
                            if response.status_code == 200:
                                self._display(f"\t{item['id']}: Create successful", self.colors.get("success", "green"))
                                changes['updated'] = {"status": "success", "data": item}
                            else:
                                if response.text.find("already exists") != -1:
                                    self._display(f"\t{item['id']}: Lookup already exists",
                                                  self.colors.get("warning", "green"))
                                    changes["updated"] = {"status": "ignored", "data": item}
                                else:
                                    self._display(f"\t{item['id']}: Failed to create. {response.text}",
                                                  self.colors.get("error"))
                                    changes["updated"] = {"status": "update_failed", "data": item,
                                                          "error": response.text}
                    changes["diff"] = json.loads(
                        DeepDiff(changes["previous"]["data"], changes["updated"]["data"]).to_json())
                    return changes
            return changes
        except Exception as e:
            self._display_error("Unhandled Exception", e)
            changes["diff"] = json.loads(
                DeepDiff(changes["previous"]["data"], changes["updated"]["data"]).to_json())
            return changes

    def simulate(self, item=None):
        changes = {"id": item["id"] if "id" in item else "Unknown",
                   "previous": {"status": "does_not_exist", "data": {}},
                   "current": {"status": "import_data", "data": item}}
        try:
            if item is None:
                item = {}
            action = f"import_{self.obj_type}"
            self._log("info", action=action,
                      item_type=self.obj_type,
                      item_id=item["id"],
                      destination=self.url,
                      group=self.group)
            result = self.export(save_file=False)
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
