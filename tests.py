import geese


class TestStatic:

    def test_version(self):
        assert geese.version.__version__ == '1.1.2'
