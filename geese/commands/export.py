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

def _write_file(export_dir, export_file, data):
    with open(os.path.join(export_dir, export_file), "w") as of:
        if export_file.endswith(".json"):
            of.write(json.dumps(data, indent=4))
        else:
            safe_dump(data, of)

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
                            _write_file(dur, filename, data)
                    else:
                        filename = f"{wg}.{args.file}"
                        data = {
                            "group": obj,
                            "object_type": wg,
                            "data": all_objects[obj][wg].copy()
                        }
                        dur = _create_dir(args.directory, obj)
                        _write_file(dur, filename, data)
        else:
            for obj in all_objects:
                print(f"Working on {obj}")
                data = {
                    "data": all_objects[obj].copy()
                }
                if args.use_namespace:
                    data["namespace"] = obj
                else:
                    data["group"] = obj
                dur = _create_dir(args.directory, obj)
                self._display(f"Writing Exported File {args.file}", colors.get("info", "blue"))
                _write_file(dur, args.file, data)
        # self._display(exported_objects, colors.get("info", "green"))
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
parser.set_defaults(handler=_export_leader, cmd="export")
