import json
import os
import yaml
from yaml import YAMLError
import geese.constants.exit_codes as ec
import argparse
import sys
from geese.constants.common_arguments import add_arguments
from geese.constants.configs import colors
from geese.utils.operations import validate_args, load_configurations, filter_groups


def _import_configurations(self, args):
    self._logger.debug("action=import_configurations")
    try:
        self._display("Importing Cribl Configurations", colors.get("info", "blue"))
        # Validate args
        ko = validate_args(self, args)
        all_objects = load_configurations(self, args, ko)
        filtered_objects = filter_groups(self, all_objects)
        self._display(f"Filtered Objects to Import, processing continues", colors.get("info", "blue"))
        if "version" in all_objects:
            filtered_objects["version"] = all_objects["version"]
        results = {}
        if args.use_namespace:
            self._display(f"Namespace Importing Not Implemented", colors.get("warning", "yellow"))
            sys.exit(ec.ALL_IS_WELL)
        else:
            self._display(f"Importing Configs to {self.destination['url']}", colors.get("info", "blue"))
            for grp in filtered_objects:
                all_good, results[grp] = self.perform_import(filtered_objects[grp])
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
add_arguments(parser, ["global", "import", "commit", "objects"])
parser.set_defaults(handler=_import_configurations, cmd="import")
