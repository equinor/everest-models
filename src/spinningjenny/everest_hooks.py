import logging

from everest.plugins import hookimpl

from spinningjenny import scripts

logger = logging.getLogger(__name__)


@hookimpl
def get_forward_models():
    return scripts.fm_jobs()
