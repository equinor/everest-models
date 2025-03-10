"""
Function that will be exposed by the plugin.

This project uses the plugin management library [pluggy](https://pluggy.readthedocs.io/en/stable/)
to expose its functions
"""

import logging
import pathlib
from importlib import import_module
from importlib.resources import files
from typing import Any, Dict, List, Sequence, Set, Type

from pydantic import BaseModel

from everest_models.forward_models import get_forward_models
from everest_models.jobs.shared.io_utils import load_supported_file_encoding

try:
    from everest.plugins import hookimpl
except ModuleNotFoundError:
    import pluggy

    hookimpl = pluggy.HookimplMarker("everest")

logger = logging.getLogger(__name__)

JOBS = "everest_models.jobs"


def _get_jobs():
    return (job.name for job in files(JOBS).iterdir() if job.name.startswith("fm_"))


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
            res[job[3:] if job.startswith("fm_") else job] = schema.get(
                "-c/--config"
            ) or schema.get("config")
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


@hookimpl
def lint_forward_model(job: str, args: Sequence[str]) -> List[str]:
    """Execute job in lint mode with the given arguments.

    Make sure there is no command in args {run, schema, lint}
    only positional or optional arguments

    Args:
        job (str): Forward model job you wish to be run in lint mode
    """
    return (
        import_module(f"{JOBS}.fm_{job}.tasks")
        .clean_parsed_data(("--lint", *args), hook_call=True)
        .errors
    )


@hookimpl
def get_forward_model_documentations() -> Dict[str, Any]:
    docs: Dict[str, Any] = {}
    for job in _get_jobs():
        cmd_name = job
        full_job_name = getattr(
            import_module(f"{JOBS}.{job}.cli"), "FULL_JOB_NAME", cmd_name
        )
        examples = getattr(import_module(f"{JOBS}.{job}.cli"), "EXAMPLES", None)
        docs[job[3:] if job.startswith("fm_") else job] = {
            "cmd_name": cmd_name,
            "examples": examples,
            "full_job_name": full_job_name,
        }
    return docs


@hookimpl
def custom_forward_model_outputs(forward_model_steps: List[str]) -> Set[str]:
    outputs = set()
    for step in forward_model_steps:
        step_name, *args = step.split()
        if step_name in get_forward_models():
            parser = import_module(
                f"{JOBS}.fm_{step_name}.parser"
            ).build_argument_parser(skip_type=True)
            options = parser.parse_args(args)
            if "output" in options and options.output:
                outputs.add(options.output)
    return outputs
