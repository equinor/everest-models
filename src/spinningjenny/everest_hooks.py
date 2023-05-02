"""
Function that will be exposed by the plugin.

This project uses the plugin management library [pluggy](https://pluggy.readthedocs.io/en/stable/)
to expose its functions
"""
import logging
import sys
from importlib import resources
from typing import Dict, List

try:
    from everest.plugins import hookimpl
except ModuleNotFoundError:
    import pluggy

    hookimpl = pluggy.HookimplMarker("everest")

logger = logging.getLogger(__name__)

FORWARD_MODEL_DIR = "forward_models"
PACKAGE = "spinningjenny"


@hookimpl
def get_forward_models() -> List[Dict[str, str]]:
    """Accumulate all `fm_` prefix sub modules in the jobs module.

    Returns:
        (List[Dict[str, str]]): A list of forward models' name (exclude prefix) and module path
    """
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
