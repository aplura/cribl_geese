import sys
import os
sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))
from geese import version
from geese.knowledge.authentication import Authentication


class TestStatic:

    def test_version(self):
        assert version.__version__ == '1.1.3'