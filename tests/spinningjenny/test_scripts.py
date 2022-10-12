import importlib.resources as rsrc
import os
import sys

import pytest

import spinningjenny
from spinningjenny import scripts


@pytest.fixture
def job_config_resources():
    if sys.version_info[1] >= 9:
        import jobs.fm_add_templates

        return (
            rsrc.files(spinningjenny).joinpath("share").joinpath("forwardmodels"),
            rsrc.files(jobs.fm_add_templates).parent,
        )
    with rsrc.path(spinningjenny, "share") as path:
        return path / "forwardmodels", path.parent.parent / "jobs"


def test_job_implementation(job_config_resources):
    config_folder, job_folder = job_config_resources
    entry_point_names = set(scripts.entry_points().keys())
    config_files = set(os.listdir(config_folder))
    job_files = set(
        os.path.splitext(f)[0][3:]
        for f in os.listdir(job_folder)
        if f.startswith("fm_")
    )
    # Check corresponding entry point made for each of the config files
    assert config_files == entry_point_names
    # Check corresponding script exists for each defined config file.
    for config_file in config_files:
        assert config_file in job_files


def test_fm_jobs():
    jobs = scripts.fm_jobs()
    job_names = set([job["name"] for job in jobs])
    entry_point_names = set(scripts.entry_points().keys())
    assert job_names == entry_point_names

    for job in jobs:
        assert f"spinningjenny/share/forwardmodels/{job['name']}" in job["path"]
