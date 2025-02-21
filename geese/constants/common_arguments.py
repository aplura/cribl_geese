# Global Arguments, that should apply to any command
import sys

from geese.constants.configs import export_cmd, tuning, import_cmd

global_arguments = {
    "--propagate": {
        "help": 'Show All Messages from the logging subsystem.',
        "action": 'store_true'
    },
    "--log-level": {
        "help": "Set the logger level",
        "choices": ['CRITICAL',
                    'FATAL',
                    'ERROR',
                    'WARN',
                    'WARNING',
                    'INFO',
                    'DEBUG'],
        "default": "WARNING"
    },
    "--config": {
        "help": "Path to the configuration file",
        "default": "./config.yaml"
    }
}

selective_arguments = {
    "import": {
        "--import-dir": {
            "help": "Import Directory",
            "default": export_cmd["directory"]
        },
        "--import-file": {
            "help": "Import filename",
            "default": export_cmd["file"]
        },
        "--conflict-resolve": {
            "help": "How to resolve conflicts",
            "default": import_cmd["resolve_conflict"],
            "choices": ['update', 'ignore']
        },
        "--save": {
            "help": "Save the results of the import",
            "action": "store_true"
        },
        "--save-file": {
            "help": "Save the results of the import to this file",
            "default": import_cmd["save_file"]
        },
        "--save-dir": {
            "help": "Save the results of the validation to this directory",
            "default": export_cmd["directory"]
        },
    },
    "commit": {
        "--commit-message": {
            "help": "Commit message if set to commit"
        },
        "--commit": {
            "help": "Commits changes after all objects are imported",
            "action": "store_true"
        },
        "--deploy": {
            "help": "Deploys the commit version to the worker or fleets.",
            "action": "store_true"
        }
    },
    "objects": {
        "--list-objects": {
            "help": "Show all objects available to the command",
            "action": 'store_true'
        },
        "--namespace": {
            "help": "Comma Separated list of namespaces to export"
        },
        "--tune-ids": {
            "help": "Exclude or include ids from this file",
            "default": tuning["file"]
        },
        "--use-namespace": {
            "help": "Import all config options with a namespace",
            "action": "store_true"
        },
        "--keep-defaults": {
            "help": "Import all config options that are default items",
            "action": "store_true"
        },
        "--all-objects": {
            "help": "Just import everything",
            "action": "store_true",
            "required": "--objects" not in sys.argv and "--list-objects" not in sys.argv
        },
        "--objects": {
            "help": "Space separated list of knowledge objects to Simulate",
            "nargs": "+",
            "required": "--all-objects" not in sys.argv and "--list-objects" not in sys.argv
        },
        "--split": {
            "help": "Flag to indicate objects were split",
            "action": "store_true"
        },
         "--directory": {
            "help": "Directory to find configurations.",
            "default": export_cmd["directory"]
        },
        "--file": {
            "help": "Filename to read from or write to.",
            "default": export_cmd["file"]
        },
    }
}


def add_arguments(parser, arguments):
    for arg in arguments:
        if arg == "global":
            for ga in global_arguments:
                parser.add_argument(ga, **global_arguments[ga])
        elif arg in list(selective_arguments.keys()):
            for ga in selective_arguments[arg]:
                parser.add_argument(ga, **selective_arguments[arg][ga])


def _fix_addresses(**kwargs):
    for headername in ('to', 'cc', 'bcc', 'from'):
        try:
            headervalue = kwargs[headername]
            if not headervalue:
                del kwargs[headername]
                continue
            elif not isinstance(headervalue, str):
                # assume it is a sequence
                headervalue = ','.join(headervalue)
        except KeyError:
            pass
        except TypeError:
            raise TypeError('string or sequence expected for "{}"'.format(
                '{} found as type {}'.format(headername,
                                             type(headervalue).__name__)))
        else:
            translation_map = {'%': '%25', '&': '%26', '?': '%3F'}
            for char, replacement in translation_map.items():
                headervalue = headervalue.replace(char, replacement)
            kwargs[headername] = headervalue
    return kwargs
