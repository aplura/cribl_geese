import sys
import os
sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))
from geese import version
from geese.knowledge.authentication import Authentication


class TestStatic:

    def test_version(self):
        assert version.__version__ == '1.1.3'

    def test_auth_env(self):
        USERNAME = "GOATS"
        TEST_KEY = "TEST_GOATS"
        os.environ[TEST_KEY] = USERNAME
        authObj = Authentication({TEST_KEY: TEST_KEY})
        username_test = authObj._get_auth_env(TEST_KEY)
        assert username_test == USERNAME

    def test_auth_file(self):
        USERNAME = "GOATS"
        TEST_KEY = "TEST_GOATS"
        authObj = Authentication({TEST_KEY: USERNAME}, TEST_KEY)
        username_test = authObj._get_auth_env(TEST_KEY)
        assert username_test == USERNAME