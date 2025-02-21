import json
import os
import yaml
from yaml import YAMLError
import geese.constants.exit_codes as ec
import argparse
import sys
from geese.constants.common_arguments import add_arguments
from geese.constants.configs import colors, import_cmd, export_cmd, tuning
from geese.utils.operations import validate, validate_knowledge, validate_args, load_configurations


def _import_configurations(self, args):
    self._logger.debug("action=import_configurations")
    try:
        self._display("Importing Cribl Configurations", colors.get("info", "blue"))
        # Validate args
        ko = validate_args(self, args)
        all_objects = load_configurations(self, args, ko)
        filtered_objects = {}
        for record in {k: v for k, v in all_objects.items() if k in ko}:
            for check_object in all_objects[record]:
                c_object = all_objects[record][check_object] if isinstance(check_object, str) else check_object
                if validate(record, c_object, self.tuning_object):
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
add_arguments(parser, ["global", "import", "commit", "objects"])
parser.set_defaults(handler=_import_configurations, cmd="import")
