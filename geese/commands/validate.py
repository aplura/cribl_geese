import json
import os
import pathlib

import requests
import yaml
from yaml import YAMLError, safe_dump
import geese.constants.exit_codes as ec
import argparse
import sys
from geese.constants.common_arguments import add_arguments
from geese.constants.configs import colors, tuning, export_cmd, validate_cmd
from geese.constants.api_specs import api_specs
from geese.utils.operations import validate, load_tuning, validate_knowledge, validate_args, load_configurations


def _validate(self, args):
    self._logger.debug("action=validate_import")
    try:
        self._display("Validating Cribl Configurations against destination", colors.get("info", "blue"))
        ko = validate_args(self, args)
        all_objects = load_configurations(self, args, ko)
        filtered_objects = {}
        for record in all_objects:
            for check_object in all_objects[record]:
                c_object = all_objects[record][check_object] if isinstance(check_object, str) else check_object
                if validate(record, c_object, self.tuning_object):
                    if record not in filtered_objects:
                        filtered_objects[record] = []
                    if args.use_namespace and "id" in c_object:
                        c_object["id"] = check_object
                    filtered_objects[record].append(c_object)
        api_spec = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..",
                                "constants",
                                "api_specs",
                                f"{args.api_version}.yaml")
        self._display(f"Loading Spec {args.api_version}", colors.get("info", "blue"))
        with open(api_spec, "r") as of:
            spec = yaml.safe_load(of)
            self.load_spec(spec)
            self.spec_file = api_spec
        self._display(f"Loading Spec {args.api_version}: Complete", colors.get("info", "blue"))
        all_good, results = self.validate(filtered_objects)
        if args.save:
            with open(os.path.join(args.import_dir, f"{args.save_file}"), "w") as of:
                if args.save_file.endswith(".json"):
                    of.write(json.dumps(results))
                else:
                    safe_dump(results, of)
        self._display("Validation Complete", colors.get("info", "green"))
    except YAMLError as err:
        self._logger.error("YAMLError: {}".format(err))
        self._display("YAML Error: {}".format(err), "red")
        sys.exit(ec.YAML_ERROR)
    except Exception as e:
        self._logger.error("Error: {}".format(e))
        self._display_error("Unspecified Error", e)
        sys.exit(ec.NOT_INIT)


parser = argparse.ArgumentParser(
    description='Validate importing Cribl Configurations to a leader',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
add_arguments(parser, ["global"])
parser.add_argument("--all-objects",
                    help="Just import everything",
                    action='store_true',
                    required='--objects' not in sys.argv and "--list-objects" not in sys.argv)
parser.add_argument("--use-namespace",
                    help="Validate all config options with a namespace",
                    action='store_true')
parser.add_argument("--api-version",
                    help="What version of the API to validate against.",
                    default=list(api_specs.keys())[0], choices=list(api_specs.keys()))
parser.add_argument("--import-dir",
                    help="Where to import the configurations from for validation:  directory",
                    default=export_cmd["directory"])
parser.add_argument("--import-file",
                    help="Where to import the configurations from for validation:  filename",
                    default=export_cmd["file"])
parser.add_argument("--save", help="Save the results of the validation", action='store_true')
parser.add_argument("--save-file",
                    help="Save the results of the validation to this file",
                    default=validate_cmd["file"])
parser.add_argument("--save-dir",
                    help="Save the results of the validation to this directory",
                    default=export_cmd["directory"])
parser.add_argument("--tune-ids", help="Exclude or include ids from this file", default=tuning["file"])
parser.add_argument("--objects",
                    help="Space separated list of knowledge objects to validate",
                    nargs='+',
                    required="--all-objects" not in sys.argv and "--list-objects" not in sys.argv)
parser.add_argument("--list-objects", help="Show all objects available to validate", action='store_true')
parser.set_defaults(handler=_validate, cmd="validate")
