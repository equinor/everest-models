"""
Function that will be exposed by the plugin.

This project uses the plugin management library [pluggy](https://pluggy.readthedocs.io/en/stable/)
to expose its functions
"""
import logging
import pathlib
import sys
from importlib import import_module, resources
from typing import Dict, List, Type

from pydantic import BaseModel

from everest_models.jobs.shared.io_utils import load_supported_file_encoding

try:
    from everest.plugins import hookimpl
except ModuleNotFoundError:
    import pluggy

    hookimpl = pluggy.HookimplMarker("everest")

logger = logging.getLogger(__name__)

FORWARD_MODEL_DIR = "forward_models"
PACKAGE = "everest_models"
JOBS = f"{PACKAGE}.jobs"


def _get_jobs():
    return (job for job in resources.contents(JOBS) if job.startswith("fm_"))


@hookimpl
def get_forward_models() -> List[Dict[str, str]]:
    """Accumulate all maintained forward model jobs by name and path.

    Returns:
        (List[Dict[str, str]]): list of forward models and corrolated path
        - {name: forward_model, path: /path/to/forward_model}
        - ...
    """
    if sys.version_info.minor >= 9:
        jobs = resources.files(PACKAGE) / FORWARD_MODEL_DIR  # type: ignore
    else:
        with resources.path(PACKAGE, FORWARD_MODEL_DIR) as fd:
            jobs = fd

    return [
        {"name": (job_name := job.lstrip("fm_")), "path": str(jobs / job_name)}
        for job in _get_jobs()
    ]


@hookimpl
def get_forward_models_schemas() -> Dict[str, Dict[str, Type[BaseModel]]]:
    """Accumulate all forward model jobs and schemas.

    group schemas by the name of forward models,
    and map them by command-line iterface option keys

    Returns:
        Dict[str, Dict[str, Type[T]]]: grouped schemas per forward model
        {
            forward_model: {
                -opt/--option: OptionModel,
                -c/--config: ConfigModel,
            },
            ...
        }
    """
    res = {}
    for job in _get_jobs():
        schema = getattr(import_module(f"{JOBS}.{job}.parser"), "SCHEMAS", None)
        if schema:
            res[job.lstrip("fm_")] = schema.get("-c/--config")
    return res


@hookimpl
def parse_forward_model_schema(path: str, schema: Type[BaseModel]) -> BaseModel:
    """Parse given filepath by the provided schema model.

    Args:
        path (str): path to the file to be parsed
        schema (Type[T]): Schema Model to parse file

    Returns:
        T: pydantic.BaseModel subclass instance
    """
    path_ = pathlib.Path(path)
    if not path_.exists() or path_.is_dir():
        raise ValueError(f"File does not exists or is a directory: {path_}")

    return schema.model_validate(load_supported_file_encoding(path_))
