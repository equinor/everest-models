import itertools
import sys

from spinningjenny import scripts


def test_hooks_registered(plugin_manager):
    assert sys.modules["spinningjenny.everest_hooks"] in plugin_manager.get_plugins()


def test_everest_hooks(plugin_manager):
    jobs = itertools.chain.from_iterable(plugin_manager.hook.get_forward_models())
    for job in scripts.fm_jobs():
        assert job in jobs
