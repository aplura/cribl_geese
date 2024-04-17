#!/usr/bin/env python3
from geese import commands
import multicommand
from geese.constants.common_arguments import global_arguments
from geese.constants import version
import sys
from geese.goose import Goose


def main():
    parser = multicommand.create_parser(commands)
    for ga in global_arguments:
        parser.add_argument(ga, **global_arguments[ga])
    parser.add_argument("--version", help="Gets the version", action='store_true')
    args = parser.parse_args()
    if args.version:
        print(f"Version: {version}")
        return
    if hasattr(args, "handler"):
        goose = Goose(args.cmd, args)
        goose.execute()
    else:
        parser.print_help()


if __name__ == "geese.main":
    sys.exit(main())
