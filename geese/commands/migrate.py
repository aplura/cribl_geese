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
from geese.knowledge import Versioning, Worker


def _migrate_workers(self, args):
    self._logger.debug("action=migrate_workers")
    self._display("NOTE: This is WIP. Use at your own risk.", colors.get("error", "red"))
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
                        workers = "\n".join(
                            [f'\t\t\t{w["id"]}: {w["info"]["hostname"]} ({w["info"]["cribl"]["distMode"]})' for w in
                             group["workers"]])
                        self._display(
                            "\n".join([f'\tGroup: {group["id"]}',
                                       f'\t\tDescription: {group["description"] if "description" in group else "No Description"}',
                                       f'\t\tWorkers ({len(group["workers"])})',
                                       workers
                                       ]),
                            colors.get("info", "blue"))
            sys.exit(ec.ALL_IS_WELL)
        else:
            groups = args.groups if args.groups else []
            workers_to_migrate = []
            for leader in self.sources:
                g = self.objects["groups"](leader, self._args, self._logger,
                                           display=self._display)
                for group in g.list_all():
                    if group['id'] in groups or args.all_groups:
                        for w in group["workers"]:
                            w["current_leader"] = leader["url"]
                            if len(args.guids) > 0 and w['id'] in args.guids:
                                workers_to_migrate.append(Worker(leader, self._args, self._logger, display=self._display, **w))
                            elif len(args.guids) == 0:
                                workers_to_migrate.append(Worker(leader, self._args, self._logger, display=self._display, **w))
            for worker in workers_to_migrate:
                wj = worker.to_json()
                try:
                    new_group = args.new_group if args.new_group != "ORIG" else wj['group']
                    self._display(f"\tMigrating worker: {wj['id']} from {wj['leader']['url']}:{wj['group']} to {self.destination['url']}:{new_group}",
                                  colors.get("info", "blue"))
                    if worker.migrate_leader(group=new_group, leader=self.destination, auto_restart=args.auto_restart):
                        self._display(f"\t\tAll Migration Tasks complete for {wj['id']}", colors.get("success", "green"))
                    else:
                        self._display(f"\t\tAll Migration Tasks complete for {wj['id']}", colors.get("error", "red"))
                except Exception as e:
                    self._display(f"\t\tError on Migration for worker {wj['id']}: {e}", colors.get("error", "red"))

    except YAMLError as err:
        self._logger.error("YAMLError: {}".format(err))
        self._display("YAML Error: {}".format(err), colors.get("error", "red"))
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
parser.add_argument("--auto-restart", help="Auto Restart each worker after update", action='store_true')
parser.add_argument("--all-groups", help="Migrate all groups, all workers (unless --single specified)",
                    action='store_true', required="--list-groups" not in sys.argv and "--groups" not in sys.argv)
parser.add_argument("--guids", help="Migrate specific worker(s) to the destination. (space separated)", default=[],
                    nargs='+',
                    required="--list-groups" not in sys.argv and "--single" in sys.argv)
parser.add_argument("--groups",
                    help="Migrate entire group(s)/fleet(s) to the destination. (space separated)",
                    nargs='+',
                    default=[],
                    required="--list-groups" not in sys.argv and "--all-groups" not in sys.argv)
parser.add_argument("--new-group",
                    help="The Destination group to place the workers in. If not specified, it will use the originating group",
                    default="ORIG")
parser.set_defaults(handler=_migrate_workers, cmd="migrate")
