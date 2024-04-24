#!/usr/bin/env python3
import os

from geese import commands
import multicommand
from geese.constants.common_arguments import global_arguments
from geese.constants import version
import sys
from geese.goose import Goose, display


def main():
    parser = multicommand.create_parser(commands)
    for ga in global_arguments:
        parser.add_argument(ga, **global_arguments[ga])
    parser.add_argument("--version", help="Displays the version", action='store_true')
    parser.add_argument("--readme", help="Displays the readme in Markdown", action='store_true')
    parser.add_argument("--license", help="Displays the License", action='store_true')
    args = parser.parse_args()
    _edir = os.path.dirname(__file__)
    print(_edir)
    if args.version:
        display(f"Version: {version}")
    if args.readme:
        with open(os.path.join(_edir, "README.md"), "r") as f:
            display(f.read(), "green")
    if args.license:
        with open(os.path.join(_edir, "LICENSE.txt"), "r") as f:
            display(f.read(), "green")
    if args.version or args.readme or args.license:
        return
    if hasattr(args, "handler"):
        goose = Goose(args.cmd, args)
        goose.execute()
    else:
        parser.print_help()


if __name__ == "geese.main":
    sys.exit(main())
