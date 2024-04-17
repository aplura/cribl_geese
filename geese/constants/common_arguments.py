# Global Arguments, that should apply to any command
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

}


def add_arguments(parser, arguments):
    for arg in arguments:
        if arg == "global":
            for ga in global_arguments:
                parser.add_argument(ga, **global_arguments[ga])
        elif arg in list(selective_arguments.keys()):
            parser.add_argument(selective_arguments[arg]["flag"], **selective_arguments[arg]["args"])


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
