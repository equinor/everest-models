from spinningjenny import fm_jobs
from everest.plugins import hookimpl


@hookimpl
def get_forward_models():
    return fm_jobs()
