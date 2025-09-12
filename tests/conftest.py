import os
import pathlib
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

import pluggy
import pytest
import rips
from hypothesis import HealthCheck, settings

sys.modules["everest.plugins"] = type(sys)("everest.plugins")
sys.modules["everest.plugins"].hookimpl = pluggy.HookimplMarker("test")

from everest_models import everest_hooks  # noqa: E402
from everest_models.jobs.shared.io_utils import (  # noqa: E402
    dump_yaml,
    load_json,
    load_yaml,
)

settings.register_profile(
    "ci",
    max_examples=250,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


def pytest_addoption(parser: Any) -> Any:
    parser.addoption(
        "--test-resinsight",
        action="store_true",
        default=False,
        help="Run ResInsight tests",
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests",
    )


def pytest_collection_modifyitems(config: Any, items: Sequence[Any]) -> None:
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    if config.getoption("--test-resinsight"):
        instance = rips.Instance.launch(console=True)
        if instance is None:
            msg = (
                "Tests marked as `resinsight` require the RESINSIGHT_EXECUTABLE environment variable, "
                "or that it is configured via the `rips` installation"
            )
            pytest.exit(msg, returncode=pytest.ExitCode.USAGE_ERROR)
        instance.exit()
    else:
        skip_resinsight = pytest.mark.skip(
            reason="need --test-resinsight option to run"
        )
        for item in items:
            if "resinsight" in item.keywords:
                item.add_marker(skip_resinsight)


class TestSpec:
    """A hook specification namespace."""

    hookspec = pluggy.HookspecMarker("test")

    @hookspec
    def get_forward_models_schemas(self): ...

    @hookspec
    def parse_forward_model_schema(self, path, schema): ...

    @hookspec
    def lint_forward_model(job, args): ...


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


@pytest.fixture(scope="session")
def reference_docs() -> pathlib.Path:
    """Path to the reference documentation directory"""
    return pathlib.Path(__file__).parent.parent / "docs/reference"


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


@pytest.fixture()
def add_wells_to_config() -> Callable[[Path | str, Path | str], None]:
    def _add_wells_to_config(input_json: Path | str, config_yaml: Path | str) -> None:
        config_dict = load_yaml(config_yaml) if Path(config_yaml).exists() else {}
        config_dict["wells"] = load_json(input_json)
        with open(config_yaml, "w") as fp:
            dump_yaml(config_dict, fp)

    return _add_wells_to_config
