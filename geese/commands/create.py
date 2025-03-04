from yaml import YAMLError
import geese.constants.exit_codes as ec
import argparse
import sys
from geese.constants.common_arguments import add_arguments


def _create_configurations(self, args):
    self._logger.debug("action=create_configurations")
    try:
        arg_lines = [f"{key}={value}" for key, value in args.__dict__.items()]
        self._logger.debug(f"action=create_configurations {' '.join(arg_lines)}")

    except YAMLError as err:
        self._logger.error("YAMLError: {}".format(err))
        self._display("YAML Error: {}".format(err), "red")
        sys.exit(ec.YAML_ERROR)
    except Exception as e:
        self._logger.error("Error: {}".format(e))
        self._display_error("Unspecified Error", e)
        sys.exit(ec.NOT_INIT)


parser = argparse.ArgumentParser(
    description='Create Cribl Configurations',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
add_arguments(parser, ["global", "create"])
parser.add_argument("--pack",
                    help="Create a pack based on a worker group configuration",
                    default=None)
parser.set_defaults(handler=_create_configurations, cmd="create")
