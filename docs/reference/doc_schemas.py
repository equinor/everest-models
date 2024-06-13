#! /usr/bin/env python
import contextlib
import os
import pathlib
import re
import subprocess
from argparse import ArgumentParser, ArgumentTypeError
from importlib import resources
from typing import List, Optional, Sequence, Tuple

from typing_extensions import Final

_FILEPATH: Final[pathlib.Path] = pathlib.Path(__file__)
REFERENCE_DIR: Final[pathlib.Path] = _FILEPATH.parent
CURRENT_FILENAME: Final[str] = _FILEPATH.name
JOBS_MODULE: Final[str] = "everest_models.jobs"
JOB_PREFIX: Final[str] = "fm_"
ARGUMENT_PREFIX: Final[str] = "--"
ARGUMENT: Final[str] = "schema"
ARGUMENT_CALL: Final[str] = f"{ARGUMENT} {ARGUMENT_PREFIX}init"
LAGECY_ARGUMENT_CALL: Final[str] = f"{ARGUMENT_PREFIX}{ARGUMENT}"


def write_to_reference_docs(job: str, references_dir: pathlib.Path) -> None:
    """Write job schema under the ./docs/references/<job>/schema.yml."""
    job_directory = references_dir / job.lstrip(JOB_PREFIX)
    job_directory.mkdir(exist_ok=True)
    try:
        subprocess.check_output(
            (job, *ARGUMENT_CALL.split()), stderr=subprocess.STDOUT, cwd=job_directory
        )
    except subprocess.CalledProcessError:
        info = subprocess.check_output(
            (job, LAGECY_ARGUMENT_CALL), stderr=subprocess.STDOUT
        )
        for match in re.finditer(
            r"(?<=---\n)(?P<content>#.*?--(?P<argument>.*?) specification:\n.*?)(?=\n\.\.\.\n)",
            info.decode(encoding=f"utf-{16 if os.name == 'tn' else 8}"),
            re.DOTALL | re.UNICODE,
        ):
            (
                job_directory / f"{match.group('argument').replace('-', '_')}.yml"
            ).write_text(match.group("content") + "\n")


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
    parser.add_argument(
        "-d",
        "--output-directory",
        type=pathlib.Path,
        help="Directory path where to export docs to",
        default=REFERENCE_DIR,
    )
    return parser


def main(args: Optional[Sequence[str]] = None) -> None:
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    for job in forward_models(options.forward_models):
        with contextlib.suppress(subprocess.CalledProcessError):
            write_to_reference_docs(job, options.output_directory)


if __name__ == "__main__":
    main()
