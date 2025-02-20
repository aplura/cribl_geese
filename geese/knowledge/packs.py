import json
import os
import shutil
import uuid
from copy import deepcopy

from deepdiff import DeepDiff
from yaml import YAMLError, safe_dump

from geese.knowledge import Secrets, CollectorJobs, Routes
from geese.knowledge.base import BaseKnowledge
from geese.utils import validate


def stz_compress(*args):
    pass


class Packs(BaseKnowledge):
    obj_type = "packs"

    def __init__(self, leader, args=None, logger=None, group=None, fleet=None, **kwargs):
        super().__init__(leader, args, logger, **kwargs)
        try:
            self.default_types = []
            self.endpoint = "packs"
            self.api_path = f"/{self.endpoint}"
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
                self._display("\tAttempting to export pack using mode=merge...",
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
        action = f"export_{self.obj_type}"
        try:
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
                        packs.append(pack)
            return packs
        except Exception as e:
            self._display_error(f"{action} Unhandled EXPORT Exception: {self.obj_type}", e)
            return []

    def _upload_and_install(self, pack, local_location=""):
        pack_id = pack["name"]
        with open(local_location, 'rb') as f:
            data = f.read()
        url = f"packs?filename={pack_id}.crbl&size={len(data)}"
        if self.group is not None:
            url = f"m/{self.group}/{url}"
        headers = deepcopy(self.headers)
        headers["Content-type"] = 'application/octet-stream'
        response = self.put(url, headers=headers, data=data)
        if response.status_code == 200:
            if "source" in response.json():
                payload = {
                    "source": response.json()["source"],
                    "force": True
                }
                return self.post(self.endpoint, payload=payload)
            else:
                return response
        else:
            return response

    def _upload_via_conf(self, pack):
        try:
            item = {"version": pack.get("settings", pack).get("version"),
                    "author": pack.get("author"),
                    "description": pack.get("description"),
                    "displayName": pack.get("displayName"),
                    "name": pack.get("id"),
                    "tags": pack.get("tags")
            }
            # route, pipelines/, <>, data/samples/, data/lookups, <>, vars, <>
            pack_valid_items = ["routes", "pipelines", "functions", "samples", "lookups", "parsers", "global_variables",
                                "schemas", "readme", "logo"]
            file_location = os.path.join(os.getcwd(), "pack")
            pack_id = item['name']
            file_name = f"{pack_id}.crbl"
            zip_file = os.path.join(file_location, file_name)
            tmp_location = os.path.join(file_location, uuid.uuid4().hex)
            default_location = os.path.join(tmp_location, "default")
            data_location = os.path.join(tmp_location, "data")
            pipeline_location = os.path.join(default_location, "pipelines")
            for d in [tmp_location, default_location, data_location]:
                if not os.path.exists(d):
                    os.makedirs(d)
            with open(os.path.join(tmp_location, "package.json"), "w") as f:
                f.write(json.dumps(item))
            for pack_item in pack_valid_items:
                if pack_item == "routes" and pack_item in pack:
                    if not os.path.exists(pipeline_location):
                        os.makedirs(pipeline_location)
                    t = pack[pack_item]
                    with open(os.path.join(pipeline_location, "route.yml"), "w") as f:
                        safe_dump(t[0], f)
                if pack_item == "pipelines" and pack_item in pack:
                    if not os.path.exists(pipeline_location):
                        os.makedirs(pipeline_location)
                    t = pack[pack_item]
                    for pipeline in t:
                        conf = t[pipeline]["conf"]
                        output_path = os.path.join(pipeline_location, pipeline)
                        if not os.path.exists(output_path):
                            os.makedirs(output_path)
                        output_file = os.path.join(output_path, "conf.yml")
                        with open(output_file, "w") as f:
                            safe_dump(conf, f)
                if pack_item == "readme" and pack_item in pack:
                    t = pack[pack_item]
                    with open(os.path.join(tmp_location, "README.md"), "w") as f:
                        f.write(f"{t}")
                if pack_item == "logo" and pack_item in pack:
                    t = pack[pack_item]
                    with open(os.path.join(tmp_location, "default", "pack.yml"), "w") as f:
                        safe_dump({"logo": f"data:image/png;base64,{pack['logo']}"}, f)
            shutil.make_archive(zip_file, 'gztar', tmp_location)
            shutil.move(f"{zip_file}.tar.gz", zip_file)
            shutil.rmtree(tmp_location)
            # Build a "pack file" (tar gz) with correct knowledge.
            # For all non-pack files, upload via "ruck" objects.
            response = self._upload_and_install(item, local_location=zip_file)
            if response.status_code == 200:
                self._display(f"\t{item['name']}: Pack Installed Successfully", self.colors.get("success", "green"))
                kit_valid_items = ["secrets", "collectors", "inputs", "routes"]
                changes = {}
                for kit_item in kit_valid_items:
                    if kit_item in pack:
                        if kit_item == "secrets":
                            self._display(f"\tProcessing ruck: Secrets", self.colors.get("info", "blue"))
                            s = Secrets(self.leader, group=self.group, args=self.args)
                            changes[kit_item] = []
                            for secret in pack[kit_item]:
                                changes[kit_item].append(s.update(pack[kit_item][secret]))
                            statuses = [True if x["updated"]["status"] == "success" else False for x in changes[kit_item]]
                            if all(statuses):
                                self._display(f"\t\t{kit_item}: ruck Objects Installed Successfully",
                                              self.colors.get("success", "green"))
                            else:
                                self._display(f"\t\t{kit_item}: Failed to install all items.",
                                              self.colors.get("error", "red"))
                        if kit_item == "collectors":
                            self._display(f"\tProcessing ruck: Collection Jobs", self.colors.get("info", "blue"))
                            s = CollectorJobs(self.leader, group=self.group, args=self.args)
                            changes[kit_item] = []
                            for job in pack[kit_item]:
                                changes[kit_item].append(s.update(pack[kit_item][job]))
                            statuses = [True if x["updated"]["status"] == "success" else False for x in changes[kit_item]]
                            if all(statuses):
                                self._display(f"\t\t{kit_item}: ruck Objects Installed Successfully", self.colors.get("success", "green"))
                            else:
                                self._display(f"\t\t{kit_item}: Failed to install all items.",
                                              self.colors.get("error", "red"))
                        if kit_item == "routes":
                            self._display(f"\tProcessing ruck: Routes", self.colors.get("info", "blue"))
                            r = Routes(self.leader, group=self.group, args=self.args)
                            changes[kit_item] = []
                            pack_route = {
                                "clones": [],
                                "description": "Routes VMWare Data to VMWare Pipelines",
                                "disabled": False,
                                "enableOutputExpression": False,
                                "filter": 'routes == "vmware"',
                                "final": True,
                                "id": 'ruck-vmware_cbc-route',
                                "name":" VMWare CBC Route",
                                "output": "default",
                                "pipeline": f"pack:{pack_id}"
                            }
                            changes[kit_item].append(r.add(pack_route))
                            statuses = [True if x["updated"]["status"] == "success" else False for x in changes[kit_item]]
                            if all(statuses):
                                self._display(f"\t\t{kit_item}: Ruck Objects Installed Successfully",
                                              self.colors.get("success", "green"))
                            else:
                                self._display(f"\t\t{kit_item}: Failed to install all items.",
                                              self.colors.get("error", "red"))
            else:
                self._display(f"\t{item['id']}: Failed to install pack.",self.colors.get("error", "red"))
            return response
        except Exception as e:
            self._display_error("Unhandled Exception", e)
            return {}

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
                response = self._upload_and_install(item, item["local_location"])
            else:
                response = self._upload_via_conf(item)
            if response.status_code == 200:
                self._display(f"\t{item['id']}: Create/Update successful", self.colors.get("success", "green"))
                changes['updated'] = {"status": "success", "data": item}
            else:
                if response.text.find("already exist") == -1:
                    # some other error
                    res = response.json()
                    msg = res.get("message", res.get("error", "Error on Message"))
                    self._display(
                        f"\t{item['id']}: Failed to create. {msg}",
                        self.colors.get("error", "red"))
                    changes["updated"] = {"status": "update_failed", "data": item,
                                          "error": msg}
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
