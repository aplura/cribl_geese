import json
import os
import yaml
from yaml import YAMLError, safe_dump
import geese.constants.exit_codes as ec
import argparse
import sys
from geese.constants.common_arguments import add_arguments
from geese.constants.configs import colors, import_cmd, tuning, export_cmd, simulate_cmd
from geese.utils.operations import validate, load_tuning, validate_knowledge


def _simulate(self, args):
    self._logger.debug("action=simulate_import")
    try:
        self._display("Simulating Simulation of Cribl Configurations", colors.get("info", "blue"))
        if not args.import_file.endswith(".yaml") and args.import_file.endswith(".json"):
            self._display(f"Simulation file: {args.import_file} is not a YAML or JSON file.", colors.get("error"))
            sys.exit(ec.FILE_NOT_FOUND)
        if args.save_file and not args.save_file.endswith(".yaml") and args.save_file.endswith(".json"):
            self._display(f"Save file: {args.save_file} is not a YAML or JSON file.", colors.get("error"))
            sys.exit(ec.FILE_NOT_FOUND)
        tuning_object = {}
        if args.tune_ids and not args.tune_ids.endswith(".yaml") and args.tune_ids.endswith(".json"):
            self._display(f"Tuning file: {args.tune_ids} is not a YAML or JSON file.", colors.get("error"))
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
            self._display(f"Export Directory does not exist: {args.import_dir}", colors.get("error", "red"))
            sys.exit(ec.LOCATION_NOT_FOUND)
        with open(os.path.join(args.import_dir, f"{args.import_file}"), "r") as of:
            if args.import_file.endswith(".json"):
                file_data = json.load(of)
            else:
                file_data = yaml.safe_load(of)
            for worker_group in file_data:
                all_objects = {k: v for k, v in file_data[worker_group].items() if k in ko}
        filtered_objects = {}
        for record in all_objects:
            for check_object in all_objects[record]:
                c_object = all_objects[record][check_object] if isinstance(check_object, str) else check_object
                if validate(record, c_object, tuning_object):
                    if record not in filtered_objects:
                        filtered_objects[record] = []
                    if args.use_namespace and "id" in c_object:
                        c_object["id"] = check_object
                    filtered_objects[record].append(c_object)
        all_good, results = self.simulate(filtered_objects)
        if args.save:
            with open(os.path.join(args.import_dir, f"{args.save_file}"), "w") as of:
                if args.save_file.endswith(".json"):
                    of.write(json.dumps(results))
                else:
                    safe_dump(results, of)
        # self._display(exported_objects, colors.get("info", "green"))
    except YAMLError as err:
        self._logger.error("YAMLError: {}".format(err))
        self._display("YAML Error: {}".format(err), "red")
        sys.exit(ec.YAML_ERROR)
    except Exception as e:
        self._logger.error("Error: {}".format(e))
        self._display_error("Unspecified Error", e)
        sys.exit(ec.NOT_INIT)


parser = argparse.ArgumentParser(
    description='Simulate importing Cribl Configurations to a leader',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
add_arguments(parser, ["global"])
parser.add_argument("--all-objects",
                    help="Just import everything",
                    action='store_true',
                    required='--objects' not in sys.argv and "--list-objects" not in sys.argv)
parser.add_argument("--use-namespace",
                    help="Simulate all config options with a namespace",
                    action='store_true')
parser.add_argument("--keep-defaults",
                    help="Keep the default types for each object",
                    action='store_true')
parser.add_argument("--import-dir",
                    help="Where to import the configurations from for simulation:  directory",
                    default=export_cmd["directory"])
parser.add_argument("--import-file",
                    help="Where to import the configurations from for simulation:  filename",
                    default=export_cmd["file"])
parser.add_argument("--conflict-resolve",
                    help="How to resolve conflicts",
                    default=import_cmd["resolve_conflict"],
                    choices=['update', 'ignore'])
parser.add_argument("--save", help="Save the results of the simulation", action='store_true')
parser.add_argument("--save-file",
                    help="Save the results of the simulation to this file",
                    default=simulate_cmd["file"])
parser.add_argument("--tune-ids", help="Exclude or include ids from this file", default=tuning["file"])
parser.add_argument("--objects",
                    help="Space separated list of knowledge objects to Simulate",
                    nargs='+',
                    required="--all-objects" not in sys.argv and "--list-objects" not in sys.argv)
parser.add_argument("--list-objects", help="Show all objects available to Simulate", action='store_true')
parser.set_defaults(handler=_simulate, cmd="simulate")
