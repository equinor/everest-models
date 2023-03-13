import logging
import sys
from importlib import resources

from everest.plugins import hookimpl

logger = logging.getLogger(__name__)

FORWARD_MODEL_DIR = "forward_models"
PACKAGE = "spinningjenny"


@hookimpl
def get_forward_models():
    if sys.version_info.minor >= 9:
        jobs = resources.files(PACKAGE) / FORWARD_MODEL_DIR
    else:
        with resources.path(PACKAGE, FORWARD_MODEL_DIR) as fd:
            jobs = fd

    return [
        {"name": (job_name := job.lstrip("fm_")), "path": str(jobs / job_name)}
        for job in resources.contents(f"{PACKAGE}.jobs")
        if job.startswith("fm_")
    ]
