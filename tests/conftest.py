import os
import pathlib
import shutil
import sys

import pluggy
import pytest
from hypothesis import HealthCheck, settings

sys.modules["everest.plugins"] = type(sys)("everest.plugins")
sys.modules["everest.plugins"].hookimpl = pluggy.HookimplMarker("test")

from everest_models import everest_hooks

settings.register_profile(
    "ci",
    max_examples=250,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


class TestSpec:
    """A hook specification namespace."""

    hookspec = pluggy.HookspecMarker("test")

    @hookspec
    def get_forward_models():
        ...

    @hookspec
    def get_forward_models_schemas():
        ...


class MockPluginManager(pluggy.PluginManager):
    """A testing plugin manager"""

    def __init__(self):
        super().__init__("test")
        self.add_hookspecs(TestSpec)


@pytest.fixture(scope="package")
def plugin_manager() -> MockPluginManager:
    pm = MockPluginManager()
    try:
        pm.register(everest_hooks)
    except ValueError as err:
        if not str(err).startswith("Plugin already registered"):
            raise err
    return pm


@pytest.fixture(scope="session")
def path_test_data() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "testdata"


@pytest.fixture
def copy_testdata_tmpdir(path_test_data, tmp_path):
    def _copy_tree(path=None):
        path = path_test_data if path is None else path_test_data / path
        shutil.copytree(path, tmp_path, dirs_exist_ok=True)

    cwd = pathlib.Path.cwd()
    os.chdir(tmp_path)
    yield _copy_tree
    os.chdir(cwd)


@pytest.fixture
def switch_cwd_tmp_path(tmp_path):
    cwd = pathlib.Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)
