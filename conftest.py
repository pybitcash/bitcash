import os
import copy
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--regtest", action="store_true", help="run test with a local regtest node"
    )


def pytest_runtest_setup(item):
    if "regtest" in item.keywords and not item.config.getoption("--regtest"):
        pytest.skip("need --regtest option to run this test")


@pytest.fixture(scope="function")
def reset_environ():
    """Reset os.environ after each test."""
    original_environ = copy.deepcopy(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original_environ)
