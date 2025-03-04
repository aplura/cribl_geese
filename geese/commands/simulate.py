import json
import os
from yaml import YAMLError, safe_dump
import geese.constants.exit_codes as ec
import argparse
import sys
from geese.constants.common_arguments import add_arguments
from geese.constants.configs import colors
from geese.utils.operations import validate_args, load_configurations, \
    filter_groups


def _simulate(self, args):
    self._logger.debug("action=simulate_import")
    try:
        self._display("Simulating Simulation of Cribl Configurations", colors.get("info", "blue"))
        ko = validate_args(self, args)
        all_objects = load_configurations(self, args, ko)
        filtered_objects = filter_groups(self, all_objects)
        self._display(f"Filtered Objects to validate", colors.get("info", "blue"))
        #  TODO: FAILS TO SIMULATE
        all_good, results = self.simulate(filtered_objects)
        if args.save:
            with open(os.path.join(args.directory, f"{args.save_file}"), "w") as of:
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
add_arguments(parser, ["global", "import", "objects"])
parser.set_defaults(handler=_simulate, cmd="simulate")
