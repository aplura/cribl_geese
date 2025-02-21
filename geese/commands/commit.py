import re
from yaml import YAMLError
import geese.constants.exit_codes as ec
import argparse
import sys
from geese.constants.common_arguments import add_arguments
from geese.constants.configs import colors
from geese.knowledge import Versioning


def _commit_configurations(self, args):
    self._logger.debug("action=commit_configurations")
    try:
        arg_lines = [f"{key}={value}" for key, value in args.__dict__.items()]
        self._logger.debug(f"action=commit_configurations {' '.join(arg_lines)}")
        if args.list_groups:
            self._display("Listing Groups", colors.get("info", "blue"))
            g = self.objects["groups"](self.destination, self._args, self._logger,
                                       display=self._display)
            for group in g.export():
                show = True
                if args.filter and re.match(args.filter, group["id"]) is None:
                    show = False
                if show:
                    self._display(
                        "\n".join([f'\t{group["id"]}',
                                   f'\t\tDescription: {group["description"] if "description" in group else "No Description"}',
                                   f'\t\tCommit Id: {group["configVersion"] if "configVersion" in group else ""}']),
                        colors.get("info", "blue"))
            sys.exit(ec.ALL_IS_WELL)
        if args.groups is not None:
            groups = args.groups
            if "ALL" in groups:
                self._logger.debug(f"action=get_all_groups deploy={args.deploy} groups={groups}")
                g = self.objects["groups"](self.destination, self._args, self._logger,
                                           display=self._display)
                groups = [x["id"] for x in g.export()]
            self._display("Committing Cribl Configurations", colors.get("info", "blue"))
            for group in groups:
                self._logger.debug(f"action=committing_group deploy={args.deploy} group={group}")
                self._display("Committing: " + group, colors.get("info", "blue"))
                vers = Versioning(self.destination, self._args, self._logger, group=group, fleet=None,
                                  display=self._display)
                vers.commit(args.commit_message, deploy=args.deploy, effective=True)
        else:
            self._display("Committing Cribl Configurations", colors.get("info", "blue"))
            self._logger.debug(f"action=committing_group deploy={args.deploy}")
            self._display("Committing default", colors.get("info", "blue"))
            vers = Versioning(self.destination, self._args, self._logger, group=None, fleet=None,
                              display=self._display)
            vers.commit(args.commit_message, deploy=args.deploy, effective=True)
    except YAMLError as err:
        self._logger.error("YAMLError: {}".format(err))
        self._display("YAML Error: {}".format(err), "red")
        sys.exit(ec.YAML_ERROR)
    except Exception as e:
        self._logger.error("Error: {}".format(e))
        self._display_error("Unspecified Error", e)
        sys.exit(ec.NOT_INIT)


parser = argparse.ArgumentParser(
    description='Commit Cribl Configurations on a leader',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
add_arguments(parser, ["global", "commit"])
parser.add_argument("--filter", help="Filter on group id", default=None)
parser.add_argument("--groups",
                    help="Space separated list of groups to commit",
                    nargs='*',
                    default=None)
parser.add_argument("--list-groups", help="Show all groups available to commit", action='store_true')
parser.set_defaults(handler=_commit_configurations, cmd="commit")
