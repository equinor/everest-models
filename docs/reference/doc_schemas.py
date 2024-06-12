#! /usr/bin/env python
import contextlib
import pathlib
import subprocess
from argparse import ArgumentParser, ArgumentTypeError
from importlib import resources
from typing import List, Optional, Sequence, Tuple

from typing_extensions import Final

_FILEPATH: Final = pathlib.Path(__file__)
REFERENCE_DIR: Final = _FILEPATH.parent
CURRENT_FILENAME = _FILEPATH.name
JOBS_MODULE: Final = "everest_models.jobs"
JOB_PREFIX: Final = "fm_"
ARGUMENT_PREFIX: Final = "--"
ARGUMENT: Final = "schema"
ARGUMENT_CALL: Final = f"{ARGUMENT} {ARGUMENT_PREFIX}init"
LAGECY_ARGUMENT_CALL: Final = f"{ARGUMENT_PREFIX}{ARGUMENT}"


def write_to_reference_docs(job: str) -> None:
    """Write job schema under the ./docs/references/<job>/schema.yml."""

    job_directory = REFERENCE_DIR / job.lstrip(JOB_PREFIX)
    job_directory.mkdir(exist_ok=True)
    try:
        subprocess.check_output(
            (job, *ARGUMENT_CALL.split()), stderr=subprocess.STDOUT, cwd=job_directory
        )
    except subprocess.CalledProcessError:
        info = subprocess.check_output(
            (job, LAGECY_ARGUMENT_CALL), stderr=subprocess.STDOUT
        )
        (job_directory / f"{ARGUMENT}.yml").write_bytes(info)


def forward_models(models: Optional[List[str]]) -> Tuple[str, ...]:
    """Get installed forward models from everest-models package resource.

    If no models given all installed forward models are return,
    otherwise return models if its a subset of installed forward models.
    """
    jobs = (
        job for job in resources.contents(JOBS_MODULE) if job.startswith(JOB_PREFIX)
    )
    if not models:
        return tuple(jobs)

    if difference := ", ".join(set(models).difference(jobs)):
        raise ArgumentTypeError(f"Did not find forward model(s): {difference}")

    return tuple(models)


def build_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="doc-schemas", description="Document forward model configuration schemas."
    )
    parser.add_argument(
        "-fm",
        "--forward-models",
        type=str,
        nargs="*",
        help="Forward models you wish to build the documentation schemas. "
        "If not specified all will be documented.",
    )
    return parser


def main(args: Optional[Sequence[str]] = None) -> None:
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    for job in forward_models(options.forward_models):
        with contextlib.suppress(subprocess.CalledProcessError):
            write_to_reference_docs(job)


if __name__ == "__main__":
    main()
