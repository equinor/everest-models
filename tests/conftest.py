import sys

import pluggy
import pytest
from hypothesis import HealthCheck, settings

sys.modules["everest.plugins"] = type(sys)("everest.plugins")
sys.modules["everest.plugins"].hookimpl = pluggy.HookimplMarker("test")

from spinningjenny import everest_hooks

settings.register_profile(
    "ci", max_examples=250, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)


class TestSpec:
    """A hook specification namespace."""

    hookspec = pluggy.HookspecMarker("test")

    @hookspec
    def get_forward_models(command):
        pass


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
