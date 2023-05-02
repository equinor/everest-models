#! /usr/bin/env python
import contextlib
import pathlib
import re
import subprocess
import sys
from importlib import resources

_FILEPATH = pathlib.Path(__file__)
REFERENCE_DIR = _FILEPATH.parent
CURRENT_FILENAME = _FILEPATH.name
JOBS_MODULE = "spinningjenny.jobs"
JOB_PREFIX = "fm_"
ARGUMENT_PREFIX = "--"
HELP_ARGUMENT = f"{ARGUMENT_PREFIX}help"
SCHEMA_ARGUMENT = f"{ARGUMENT_PREFIX}schema"


def write_to_doc(job: str, argument: str, encoding: str = "utf-8") -> None:
    job_id = job.lstrip(JOB_PREFIX)
    info = subprocess.check_output(
        [sys.executable, "-m", f"{JOBS_MODULE}.{job}", argument],
        stderr=subprocess.STDOUT,
    )
    if argument == HELP_ARGUMENT:
        info = re.sub(
            bytes(r"(?<=usage: )(__main__.py|-m)", encoding),
            bytes(job_id, encoding),
            info,
        )
    job_directory = REFERENCE_DIR / job_id
    job_directory.mkdir(exist_ok=True)

    (
        job_directory
        / f"{argument.lstrip(ARGUMENT_PREFIX)}{'' if argument == HELP_ARGUMENT else '.yml'}"
    ).write_bytes(info)


for job in resources.contents(JOBS_MODULE):
    if not job.startswith(JOB_PREFIX):
        continue
    with contextlib.suppress(subprocess.CalledProcessError):
        write_to_doc(job, HELP_ARGUMENT)
        write_to_doc(job, SCHEMA_ARGUMENT)
