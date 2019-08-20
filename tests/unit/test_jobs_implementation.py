from os import listdir, path

from tests import relpath

from spinningjenny.bin import entry_points
from spinningjenny import fm_jobs

CONFIG_FOLDER = relpath("share", "spinningjenny", "forwardmodels")
SCRIPT_FOLDER = relpath("spinningjenny", "script")


def test_job_implementation():
    entry_point_names = set(entry_points().keys())
    config_files = set(listdir(CONFIG_FOLDER))
    script_files = set(
        path.splitext(f)[0][3:] for f in listdir(SCRIPT_FOLDER) if f.startswith("fm_")
    )
    # Check corresponding entry point made for each of the config files
    assert config_files == entry_point_names
    # Check corresponding script exists for each defined config file.
    for config_file in config_files:
        assert config_file in script_files


def test_fm_jobs():
    jobs = fm_jobs()
    job_names = set([job["name"] for job in jobs])
    entry_point_names = set(entry_points().keys())
    assert job_names == entry_point_names

    for job in jobs:
        assert (
            "/share/spinningjenny/forwardmodels/{}".format(job["name"]) in job["path"]
        )
