import os
import pathlib
import shutil
import sys
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Callable, Final, Iterator, Sequence
from unittest.mock import patch

import pytest
import rips
from hypothesis import HealthCheck, settings

_HAVE_ERT: Final = find_spec("ert") is not None
if _HAVE_ERT:
    # The order of these imports is important to ensure that the hookimpl marker
    # is mocked before everest_hooks is imported
    import everest.plugins  # noqa: F401
    import pluggy
    from ert.plugins import ErtRuntimePlugins

    sys.modules["everest.plugins"].hookimpl = pluggy.HookimplMarker("test")

    from everest_models import everest_hooks  # noqa: E402


settings.register_profile(
    "ci",
    max_examples=250,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@pytest.fixture()
def use_site_configurations_with_no_queue_options():
    def ErtRuntimePluginsWithNoQueueOptions(**kwargs):
        return ErtRuntimePlugins(**(kwargs | {"queue_options": None}))

    with patch(
        "ert.plugins.plugin_manager.ErtRuntimePlugins",
        ErtRuntimePluginsWithNoQueueOptions,
    ):
        yield


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


if _HAVE_ERT:

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
def switch_cwd_tmp_path(tmp_path):
    cwd = pathlib.Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)


@pytest.fixture
def copy_testdata_tmpdir(
    path_test_data: Path, tmp_path: Path
) -> Iterator[Callable[[str | None], Path]]:
    def _copy_tree(path: str | None = None):
        path_ = path_test_data if path is None else path_test_data / path
        shutil.copytree(path_, tmp_path, dirs_exist_ok=True)
        return path_

    cwd = Path.cwd()
    os.chdir(tmp_path)
    yield _copy_tree
    os.chdir(cwd)


def relpath(*path):
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), *path)


@pytest.fixture
def copy_eightcells_test_data_to_tmp(tmp_path, monkeypatch):
    path = relpath("tests", "testdata", "eightcells")
    shutil.copytree(path, tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)
