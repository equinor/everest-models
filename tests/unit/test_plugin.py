import sys
from itertools import chain

import pluggy
import pytest

# On Python3 we can mock the everest.plugins module:
sys.modules["everest.plugins"] = type(sys)("everest.plugins")
sys.modules["everest.plugins"].hookimpl = pluggy.HookimplMarker("test")

from spinningjenny import everest_hooks, fm_jobs


class TestSpec:
    """A hook specification namespace."""

    hookspec = pluggy.HookspecMarker("test")

    @hookspec
    def get_forward_models():
        pass


class MockPluginManager(pluggy.PluginManager):
    """A testing plugin manager"""

    def __init__(self):
        super().__init__("test")
        self.add_hookspecs(TestSpec)


def test_hooks_registered():
    pm = MockPluginManager()
    try:
        pm.register(everest_hooks)
    except ValueError as err:
        if not str(err).startswith("Plugin already registered"):
            raise err
    assert any(
        [
            hook.plugin_name.startswith("spinningjenny")
            for hook in pm.hook.get_forward_models.get_hookimpls()
        ]
    )


def test_everest_hooks():
    pm = MockPluginManager()
    try:
        pm.register(everest_hooks)
    except ValueError as err:
        if not str(err).startswith("Plugin already registered"):
            raise err
    jobs = chain.from_iterable(pm.hook.get_forward_models())
    for job in fm_jobs():
        assert job in jobs
