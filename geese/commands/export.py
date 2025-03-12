import csv
import json
import os
from yaml import YAMLError, safe_dump
import geese.constants.exit_codes as ec
import argparse
import sys
from geese.utils.operations import validate_args, validate_knowledge
from geese.constants.common_arguments import add_arguments
from geese.constants.configs import colors, export_cmd, tuning
# Check for a "get diff" api call

def _create_dir(export_dir, grp, namespace=None):
    dur = os.path.join(export_dir, namespace, grp, "configs") if namespace else os.path.join(export_dir, grp, "configs")
    if not os.path.exists(dur):
        os.makedirs(dur)
    return dur

def _write_file(self, export_dir, export_file, data, args):
    if not args.lookup_only:
        with open(os.path.join(export_dir, export_file), "w") as of:
            self._display(f"Writing Exported File {export_file}", colors.get("info", "blue"))
            if export_file.endswith(".json"):
                of.write(json.dumps(data, indent=4))
            else:
                safe_dump(data, of)

def _build_lookup_item(type, data):
    # Should have 3 columns. type,id,name,description
    if type in ["system_auth"]:
        return []
    default_id = "id_not_found"
    default_name = "name_not_found"
    default_description = "description_not_found"
    default_parent = "cribl"
    item = {"type": type, "id": default_id, "name": default_name, "parent": default_parent, "description": default_description}
    if type in ["routes"]:
        item = [{"type": type, "id": data.get("id", default_id), "name": data.get("name", default_name), "parent": default_parent, "description": data.get("description", default_description)}]
        for rts in data.get("routes", []):
            item.append({"type": f"{type}_route", "id": rts.get("id", default_id), "name": rts.get("name", default_name), "parent": data.get("id", default_id), "description": data.get("description", default_description)})
    else:
        item["id"] = data.get("id", default_id)
        item["name"] = data.get("name", default_name)
        item["description"] = data.get("description", default_description)
        if type in ["pipelines"]:
            item["name"] = item["id"]
            item = [item]
            for i, f in enumerate(data.get('conf', {}).get('functions', [])):
                item.append({"type": f"{type}_function", "id": f'{i}_{f.get("id", default_id)}', "name": f.get("name", default_name), "parent": item[0].get("id", default_id), "description": f.get("description", default_description)})
    return item

def _write_lookup(self, export_dir, export_file, data, args):
    lookup_items = []
    lookup_header = ["type", "id", "name", "parent", "description"]
    for o in data:
        obj = o.get("data", [])
        if not args.split and not args.use_namespace:
            for k in obj:
                for i in obj[k]:
                    r = _build_lookup_item(k, obj[k][i])
                    if type(r) is list:
                        [lookup_items.append(rd) for rd in r]
                    else:
                        lookup_items.append(r)
        elif args.split:
            t = o.get("object_type", "unknown")
            for i in obj:
                r =_build_lookup_item(t, obj[i])
                if type(r) is list:
                    [lookup_items.append(rd) for rd in r]
                else:
                    lookup_items.append(r)
        else:
            for wg in obj:
                for t in obj[wg]:
                    for i in obj[wg][t]:
                        r = _build_lookup_item(t, obj[wg][t][i])
                        if type(r) is list:
                            [lookup_items.append(rd) for rd in r]
                        else:
                            lookup_items.append(r)
    with open(os.path.join(export_dir, export_file), "w", newline='') as of:
        self._display(f"\tWriting Lookup File {export_file}", colors.get("info", "blue"))
        writer = csv.DictWriter(of, fieldnames=lookup_header)
        writer.writeheader()
        writer.writerows(lookup_items)
        # of.write(data)

def _export_leader(self, args):
    self._logger.debug("action=export_leader")
    try:
        self._display("Exporting Cribl Configurations", colors.get("info", "blue"))
        ko = validate_args(self, args)
        self._dbg(action="exporting_objects", objects=ko)
        exported_objects = self.get(ko, args.namespace)
        self._display("Exporting Knowledge Objects", colors.get("info", "blue"))
        all_objects = {}
        for obj in exported_objects:
            if obj not in all_objects and args.use_namespace:
                all_objects[obj] = {}
            for record in list(exported_objects[obj].keys()):
                oo = exported_objects[obj][record].copy()
                if len(oo) > 0:
                    if not args.use_namespace and record not in all_objects:
                        all_objects[record] = {}
                    elif record not in all_objects and args.use_namespace:
                        all_objects[obj][record] = {}
                    if args.use_namespace:
                        c_obj = all_objects[obj][record]
                    else:
                        c_obj = all_objects[record]
                    for oop in oo:
                        if len(oo[oop]) > 0:
                            if oop not in c_obj:
                                c_obj[oop] = {}
                            for item in oo[oop]:
                                id_id = None
                                for my_id in ["id", "keyId", "tenantId"]:
                                    if my_id in item:
                                        id_id = item[my_id]
                                if id_id is not None:
                                    if id_id not in c_obj[oop]:
                                        c_obj[oop][id_id] = item
                                    else:
                                        c_obj[oop][f"{obj}-{id_id}"] = item
                                else:
                                    self._display(f"Could not find ID field in item: {item}", colors.get("warning", "yellow"))
                                    k = f"{obj}-unknown_id"
                                    if k not in c_obj[oop]:
                                        c_obj[oop][k] = []
                                    c_obj[oop][k].append(item)
        if not os.path.exists(args.directory):
            os.makedirs(args.directory)
        lookup_data = []
        if args.split:
            for obj in all_objects:
                for wg in all_objects[obj]:
                    if args.use_namespace:
                        for ns in all_objects[obj][wg]:
                            filename = f"{ns}.{args.file}"
                            data = {
                                "namespace": obj,
                                "group": wg,
                                "object_type": ns,
                                "data": all_objects[obj][wg][ns].copy()
                            }
                            dur = _create_dir(args.directory, wg, obj)
                            lookup_data.append(data)
                            _write_file(self, dur, filename, data, args)
                    else:
                        filename = f"{wg}.{args.file}"
                        data = {
                            "group": obj,
                            "object_type": wg,
                            "data": all_objects[obj][wg].copy()
                        }
                        dur = _create_dir(args.directory, obj)
                        lookup_data.append(data)
                        _write_file(self, dur, filename, data, args)
        else:
            for obj in all_objects:
                data = {
                    "data": all_objects[obj].copy()
                }
                if args.use_namespace:
                    data["namespace"] = obj
                else:
                    data["group"] = obj
                dur = _create_dir(args.directory, obj)
                lookup_data.append(data)
                _write_file(self, dur, args.file, data, args)
        # self._display(exported_objects, colors.get("info", "green"))
        if args.id_lookup:
            l_file = args.id_lookup
            self._display(f"Saving Lookup IDs to {l_file}", colors.get("info", "blue"))
            _write_lookup(self, args.directory, l_file, lookup_data, args)
        self._display("Export Complete", colors.get("success", "green"))
    except YAMLError as err:
        self._logger.error("YAMLError: {}".format(err))
        self._display("YAML Error: {}".format(err), "red")
        sys.exit(ec.YAML_ERROR)
    except Exception as e:
        self._logger.error("Error: {}".format(e))
        self._display_error("Unspecified Error", e)
        sys.exit(ec.NOT_INIT)


parser = argparse.ArgumentParser(
    description='Export Cribl Configurations from a leader',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
add_arguments(parser, ["global", "objects"])
parser.add_argument("--id-lookup",
                    help="Pass a filename to save the ids with readable names.",
                    default=None)
parser.add_argument("--lookup-only",
                    help="Do not export objects, but only ID lookup.",
                    action="store_true")
parser.set_defaults(handler=_export_leader, cmd="export")
