import pytest


def pytest_addoption(parser):
    parser.addoption("--regtest", action="store_true",
                     help="run test with a local regtest node")


def pytest_runtest_setup(item):
    if 'regtest' in item.keywords and not item.config.getoption("--regtest"):
        pytest.skip("need --regtest option to run this test")
