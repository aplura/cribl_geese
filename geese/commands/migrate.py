import json
import os
import re

import yaml
from yaml import YAMLError, safe_dump
import geese.constants.exit_codes as ec
import argparse
import sys
from geese.constants.common_arguments import add_arguments
from geese.constants.configs import colors
from geese.knowledge import Versioning


def _migrate_workers(self, args):
    self._logger.debug("action=migrate_workers")
    self._display("NOTE: This is WIP. Use at your own risk.", colors["red"])
    try:
        arg_lines = [f"{key}={value}" for key, value in args.__dict__.items()]
        self._logger.debug(f"action=migrate_workers {' '.join(arg_lines)}")
        if args.list_groups:
            for leader in self.sources:
                self._display(f"Listing Groups for {leader['url']}", colors.get("info", "blue"))
                g = self.objects["groups"](leader, self._args, self._logger,
                                           display=self._display)
                for group in g.list_all():
                    show = True
                    if args.filter and re.match(args.filter, group["id"]) is None:
                        show = False
                    if show:
                        workers = "\n".join([f'\t\t\t{w["id"]}: {w["info"]["hostname"]} ({w["info"]["cribl"]["distMode"]})' for w in group["workers"]])
                        self._display(
                            "\n".join([f'\tGroup: {group["id"]}',
                                       f'\t\tDescription: {group["description"] if "description" in group else "No Description"}',
                                       f'\t\tWorkers ({len(group["workers"])})',
                                       workers
                                       ]),
                            colors.get("info", "blue"))
            sys.exit(ec.ALL_IS_WELL)

    except YAMLError as err:
        self._logger.error("YAMLError: {}".format(err))
        self._display("YAML Error: {}".format(err), "red")
        sys.exit(ec.YAML_ERROR)
    except Exception as e:
        self._logger.error("Error: {}".format(e))
        self._display_error("Unspecified Error", e)
        sys.exit(ec.NOT_INIT)


parser = argparse.ArgumentParser(
    description='Migrate Cribl Workers to a new leader',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
add_arguments(parser, ["global"])
parser.add_argument("--filter", help="Filter on group id", default=None)
parser.add_argument("--list-groups", help="Show all groups available to migrate", action='store_true')
parser.set_defaults(handler=_migrate_workers, cmd="migrate")
