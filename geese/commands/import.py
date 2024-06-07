import json
import os
import yaml
from yaml import YAMLError
import geese.constants.exit_codes as ec
import argparse
import sys
from geese.constants.common_arguments import add_arguments
from geese.constants.configs import colors, import_cmd, export_cmd, tuning
from geese.utils.operations import validate, load_tuning, validate_knowledge


def _import_configurations(self, args):
    self._logger.debug("action=import_configurations")
    try:
        self._display("Importing Cribl Configurations", colors.get("info", "blue"))
        if not args.import_file.endswith(".yaml") and args.import_file.endswith(".json"):
            self._display(f"Import file: {args.export_file} is not a YAML or JSON file.", colors.get("error"))
            sys.exit(ec.FILE_NOT_FOUND)
        if args.save_file and not args.save_file.endswith(".yaml") and args.save_file.endswith(".json"):
            self._display(f"Save file: {args.export_file} is not a YAML or JSON file.", colors.get("error"))
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
        if not os.path.exists(args.import_dir):
            self._display(f"Import Directory does not exist: {args.import_dir}", colors.get("error", "red"))
            sys.exit(ec.LOCATION_NOT_FOUND)
        with open(os.path.join(args.import_dir, f"{args.import_file}"), "r") as of:
            if args.import_file.endswith(".json"):
                file_data = json.load(of)
            else:
                file_data = yaml.safe_load(of)
            for worker_group in file_data:
                all_objects = {k: v for k, v in file_data[worker_group].items() if k in ko}
        filtered_objects = {}
        for record in {k: v for k, v in all_objects.items() if k in ko}:
            for check_object in all_objects[record]:
                c_object = all_objects[record][check_object] if isinstance(check_object, str) else check_object
                if validate(record, c_object, tuning_object):
                    if record not in filtered_objects:
                        filtered_objects[record] = []
                    if args.use_namespace and "id" in c_object:
                        c_object["id"] = check_object
                    filtered_objects[record].append(c_object)
        if "version" in all_objects:
            filtered_objects["version"] = all_objects["version"]
        all_good, results = self.perform_import(filtered_objects)
        if args.save:
            with open(os.path.join(args.import_dir, f"{args.save_file}"), "w") as of:
                if args.save_file.endswith(".json"):
                    of.write(json.dumps(results))
                else:
                    yaml.safe_dump(results, of)
    except YAMLError as err:
        self._logger.error("YAMLError: {}".format(err))
        self._display("YAML Error: {}".format(err), "red")
        sys.exit(ec.YAML_ERROR)
    except Exception as e:
        self._logger.error("Error: {}".format(e))
        self._display_error("Unspecified Error", e)
        sys.exit(ec.NOT_INIT)


parser = argparse.ArgumentParser(
    description='Import Cribl Configurations to a leader',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
add_arguments(parser, ["global"])
parser.add_argument("--all-objects",
                    help="Just import everything",
                    action='store_true',
                    required='--objects' not in sys.argv and "--list-objects" not in sys.argv)
parser.add_argument("--use-namespace", help="Import all config options with a namespace", action='store_true')
parser.add_argument("--keep-defaults", help="Import all config options that are default items", action='store_true')
parser.add_argument("--import-dir", help="Import directory", default=export_cmd["directory"])
parser.add_argument("--import-file", help="Import filename", default=export_cmd["file"])
parser.add_argument("--conflict-resolve", help="How to resolve conflicts",
                    default=import_cmd["resolve_conflict"],
                    choices=['update', 'ignore'])
parser.add_argument("--save", help="Save the results of the import", action='store_true')
parser.add_argument("--save-file", help="Save the results of the import to this file", default=import_cmd["file"])
parser.add_argument("--commit-message", help="Commit message if set to commit")
parser.add_argument("--commit", help="Commits changes after all objects are imported", action='store_true')
parser.add_argument("--deploy", help="Deploys the commit version to the worker or fleets.", action='store_true')
parser.add_argument("--tune-ids", help="Exclude or include ids from this file", default=tuning["file"])
parser.add_argument("--objects",
                    help="Space separated list of knowledge objects to import",
                    nargs='+',
                    required="--all-objects" not in sys.argv and "--list-objects" not in sys.argv)
parser.add_argument("--list-objects", help="Show all objects available to import", action='store_true')
parser.set_defaults(handler=_import_configurations, cmd="import")
