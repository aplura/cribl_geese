import json
import os

from yaml import YAMLError, safe_dump
import geese.constants.exit_codes as ec
import argparse
import sys

from geese.utils.operations import validate, load_tuning, validate_knowledge
from geese.constants.common_arguments import add_arguments
from geese.constants.configs import colors, export_cmd, tuning, import_cmd

# Check for a "get diff" api call


def _export_leader(self, args):
    self._logger.debug("action=export_leader")
    try:
        self._display("Exporting Cribl Configurations", colors.get("info", "blue"))
        if not args.export_file.endswith(".yaml") and not args.export_file.endswith(".json"):
            self._display(f"Export file: {args.export_file} is not a YAML or JSON file.", colors.get("error"))
            sys.exit(ec.FILE_NOT_FOUND)
        tuning_object = {}
        if args.tune_ids and not args.tune_ids.endswith(".yaml") and args.tune_ids.endswith(".json"):
            self._display(f"Tuning file: {args.export_file} is not a YAML or JSON file.", colors.get("error"))
            sys.exit(ec.FILE_NOT_FOUND)
        elif args.tune_ids:
            tuning_object = load_tuning(args.tune_ids)
        self.tuning_object = tuning_object
        knowledge_objects = list(self.objects.keys())
        if args.list_objects:
            self._display(f"Available objects: {', '.join(knowledge_objects)}", colors.get("info", "blue"))
            sys.exit(ec.ALL_IS_WELL)
        ko = knowledge_objects if args.all_objects else [a for a in args.objects if a in knowledge_objects and validate_knowledge(
            a, self.tuning_object)]
        exported_objects = self.get(ko)
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
                                for my_id in ["id", "keyId"]:
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
        if not os.path.exists(args.export_dir):
            os.makedirs(args.export_dir)
        with open(os.path.join(args.export_dir, f"{args.export_file}"), "w") as of:
            if args.export_file.endswith(".json"):
                of.write(json.dumps(all_objects))
            else:
                safe_dump(all_objects, of)
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
add_arguments(parser, ["global"])
# parser.add_argument("--simulate", help="Basically, a dry run", action='store_true')
parser.add_argument("--all-objects",
                    help="Just export everything",
                    action='store_true',
                    required='--objects' not in sys.argv and "--list-objects" not in sys.argv)
parser.add_argument("--use-namespace", help="Export all config options with a namespace", action='store_true')
parser.add_argument("--keep-defaults", help="Export all config options that are default items", action='store_true')
parser.add_argument("--export-dir", help="Export directory", default=export_cmd["directory"])
parser.add_argument("--export-file", help="Export filename", default=export_cmd["file"])
parser.add_argument("--tune-ids", help="Exclude or include ids from this file", default=tuning["file"])
parser.add_argument("--objects",
                    help="Space separated list of knowledge objects to export",
                    nargs='+',
                    required="--all-objects" not in sys.argv and "--list-objects" not in sys.argv)
parser.add_argument("--list-objects", help="Show all objects available to export", action='store_true')
parser.set_defaults(handler=_export_leader, cmd="export")
