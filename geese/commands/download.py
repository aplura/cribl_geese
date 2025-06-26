import pathlib
import re
from yaml import YAMLError
import geese.constants.exit_codes as ec
import argparse
import sys
from geese.constants.common_arguments import add_arguments
from requests_html import HTMLSession
import geese.constants.api_specs as aspecs
from geese.constants import version
from geese.constants.configs import colors
from geese.knowledge import Versioning

action = "download"
def _get_docs_page(self, dest):
    api_path = "https://cdn.cribl.io/dl/{0}/cribl-apidocs-{0}-{1}.yml"
    headers = {
        "user-agent": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/110.0 Geese/{version}"
    }
    session = HTMLSession()
    for idx, vers in enumerate(aspecs.api_specs):
        url = api_path.format(vers, aspecs.api_specs[vers])
        base = session.get(url, headers=headers)
        output_file = f"{vers}.yaml"
        fop = pathlib.Path(dest, output_file)
        if not fop.exists():
            fop.parent.mkdir(parents=True, exist_ok=True)
        with open(fop, "w+", encoding="utf-8") as t:
            t.write(base.text)
        self._display(f"Downloaded API Spec for {vers} from: {url}", colors.get("info", "blue"))
    # https://cdn.cribl.io/dl/4.9.3/cribl-apidocs-4.9.3-25d56bdd.yml

def _download(self, args):
    self._logger.debug(f"action={action}")
    try:
        arg_lines = [f"{key}={value}" for key, value in args.__dict__.items()]
        self._logger.debug(f"action={action} {' '.join(arg_lines)}")
        if args.api_spec:
            _get_docs_page(self, args.dest)
    except YAMLError as err:
        self._logger.error("YAMLError: {}".format(err))
        self._display("YAML Error: {}".format(err), "red")
        sys.exit(ec.YAML_ERROR)
    except Exception as e:
        self._logger.error("Error: {}".format(e))
        self._display_error("Unspecified Error", e)
        sys.exit(ec.NOT_INIT)


parser = argparse.ArgumentParser(
    description='Download various knowledge objects or specifications.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
add_arguments(parser, ["global"])
parser.add_argument("--api-spec", help="Download API Specs to help with validation", action='store_true', required=False)
parser.add_argument("--dest", help="Destination folder for downloaded files", default="download", required=False)
parser.set_defaults(handler=_download, cmd="commit")
