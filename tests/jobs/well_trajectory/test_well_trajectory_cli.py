from pathlib import Path

import pytest
from sub_testdata import WELL_TRAJECTORY as TEST_DATA

from everest_models.jobs.fm_well_trajectory.cli import main_entry_point


@pytest.fixture(scope="module")
def well_trajectory_arguments():
    return ("-c config.yml").split()


@pytest.fixture(scope="module")
def well_trajectory_output_files():
    return (
        "well_geometry.txt",
        "wellpaths/OP_4.dev",
        "wellpaths/WI_1.dev",
        "PATH_OP_4.txt",
        "PATH_WI_1.txt",
        "guide_points.json",
    )


def test_well_trajectory_main_entry_point(
    well_trajectory_arguments, well_trajectory_output_files, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)
    main_entry_point(well_trajectory_arguments)

    assert all(
        path.read_bytes() == path.with_suffix(f"{path.suffix}.expected").read_bytes()
        for path in map(Path, well_trajectory_output_files)
    )


def test_well_trajectory_main_entry_point_lint(
    well_trajectory_arguments, well_trajectory_output_files, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit):
        main_entry_point([*well_trajectory_arguments, "--lint"])

    assert not any(path.exists() for path in map(Path, well_trajectory_output_files))
