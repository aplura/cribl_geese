import json
import os

from deepdiff import DeepDiff
from geese.knowledge.base import BaseKnowledge
from geese.utils import validate


class Packs(BaseKnowledge):
    def __init__(self, leader, args=None, logger=None, group=None, fleet=None, **kwargs):
        super().__init__(leader, args, logger, **kwargs)
        try:
            self.obj_type = "packs"
            self.default_types = []
            self.endpoint = "packs"
            self.group = None
            if group is not None or fleet is not None:
                self.group = fleet if fleet is not None else group
                self.endpoint = f"m/{self.group}/packs"
        except Exception as e:
            self._display_error("Unhandled INIT Exception", e)

    def _get_pack_routes(self, pack_id):
        url = f"p/{pack_id}/routes"
        if self.group is not None:
            url = f"m/{self.group}/{url}"
        return self.get(url)

    def _get_pack_pipelines(self, pack_id):
        url = f"p/{pack_id}/pipelines"
        if self.group is not None:
            url = f"m/{self.group}/{url}"
        return self.get(url)

    def _export_pack_merge(self, pack_id):
        url = f"packs/{pack_id}/export?mode=merge"
        if self.group is not None:
            url = f"m/{self.group}/{url}"
        return self.get(url)

    def _export_pack_merge_safe(self, pack_id):
        url = f"packs/{pack_id}/export?mode=merge_safe"
        if self.group is not None:
            url = f"m/{self.group}/{url}"
        return self.get(url)

    def save_pack(self, directory, pack):
        pack_id = pack["id"]
        if not os.path.exists(directory):
            os.makedirs(directory)
        response = self._export_pack_merge_safe(pack_id)
        if response is not None and response.status_code != 200:
            if response.text.find("Use a different export mode") != -1:
                self._display(
                    f"\tPack {pack_id}: API responded with error: {json.loads(response.text)['message']}",
                    self.colors.get("error", "yellow"))
                self._display(f"\tAttempting to export pack using mode=merge...",
                              self.colors.get("warning", "yellow"))
                # try merge
                response = self._export_pack_merge(pack_id)
                if response.status_code == 200:
                    pack["local_location"] = os.path.join(directory, f"{pack_id}.crbl")
                    with open(pack["local_location"], "wb") as pack_file:
                        pack_file.write(response.content)
                    self._display(
                        f"\tPack {pack_id}: Successfully exported to {directory}",
                        self.colors.get("info", "green"))
                else:
                    self._display(f"\tPack {pack_id}: Could not download pack.",
                                  self.colors.get("error", "red"))
            else:
                self._display(
                    f"\tPack {pack_id}: Error on download. API responded with error: {json.loads(response.text)['message']}",
                    self.colors.get("error", "red"))
        elif response is not None and response.status_code == 200:
            pack["local_location"] = os.path.join(directory, f"{pack_id}.crbl")
            with open(pack["local_location"], "wb") as pack_file:
                pack_file.write(response.content)
            self._display(
                f"\tPack {pack_id}: Successfully exported pack to {directory}",
                self.colors.get("info", "green"))
        else:
            self._display(f"Unexpected response: {response}")
        return pack

    def export(self, save_pack=True):
        try:
            action = f"export_{self.obj_type}"
            data = self.get(self.endpoint)
            packs = []
            if data.status_code == 200 and data.json():
                for pack in data.json()["items"]:
                    p_id = pack["id"]
                    if validate("packs", pack, self.tuning):
                        routes_data = self._get_pack_routes(p_id)
                        routes = []
                        if routes_data.status_code == 200 and routes_data.json():
                            routes = routes_data.json()["items"]
                        pipelines = []
                        pipelines_data = self._get_pack_pipelines(p_id)
                        if pipelines_data.status_code == 200 and pipelines_data.json():
                            pipelines = pipelines_data.json()["items"]
                        pack["routes"] = routes
                        pack["pipelines"] = pipelines
                        if save_pack:
                            directory = os.path.join(self.args.export_dir, "packs")
                            self.save_pack(directory, pack)
            return packs
        except Exception as e:
            self._display_error(f"Unhandled EXPORT Exception: {self.obj_type}", e)
            return []

    def _upload_and_install(self, pack):
        pack_id = pack["id"]
        url = f"packs?filename={pack_id}"
        if self.group is not None:
            url = f"m/{self.group}/{url}"
        response = self.put(url, data=open(pack["local_location"], 'rb'))
        if response.status_code == 200:
            if "source" in response.json():
                payload = {
                    "source": response.json()["source"]
                }
                return self.post(self.endpoint, payload=payload)
            else:
                return response
        else:
            return response

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
                response = self._upload_and_install(item)
                if response.status_code == 200:
                    self._display(f"\t{item['id']}: Create successful", self.colors.get("success", "green"))
                    changes['updated'] = {"status": "success", "data": item}
                else:
                    if response.text.find("already exist") == -1:
                        # some other error
                        self._display(
                            f"\t{item['id']}: Failed to create. {json.loads(response.text)['message']}",
                            self.colors.get("error"))
                        changes["updated"] = {"status": "update_failed", "data": item,
                                              "error": json.loads(response.text)["message"]}
                    else:
                        self._display(f"\t{item['id']}: Pack already exists",
                                      self.colors.get("warning", "green"))
                        changes["updated"] = {"status": "ignored", "data": item}
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
            result = self.export(save_pack=False)
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
