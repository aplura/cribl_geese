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
from geese.constants.configs import colors
from geese.constants.api_specs import api_specs
from geese.utils.operations import  validate_args, load_configurations, \
    filter_groups


def _validate(self, args):
    self._logger.debug("action=validate_import")
    try:
        self._display("Validating Cribl Configurations against destination", colors.get("info", "blue"))
        ko = validate_args(self, args, cmd="validate")
        all_objects = load_configurations(self, args, ko)
        filtered_objects = filter_groups(self, all_objects)
        self._display(f"Filtered Objects to validate", colors.get("info", "blue"))
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
        self._display(f"Validating Cribl Working Group Configs: {', '.join(list(filtered_objects.keys()))}", colors.get("info", "blue"))
        all_good, results = self.validate(filtered_objects)
        if args.save:
            with open(os.path.join(args.directory, f"{args.save_file}"), "w") as of:
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
add_arguments(parser, ["global", "import", "objects"])
parser.add_argument("--api-version",
                    help="What version of the API to validate against.",
                    default=list(api_specs.keys())[0], choices=list(api_specs.keys()))
parser.set_defaults(handler=_validate, cmd="validate")
