import filecmp
from pathlib import Path

import pytest
from sub_testdata import WELL_TRAJECTORY as TEST_DATA

from everest_models.jobs.fm_well_trajectory.cli import main_entry_point
from everest_models.jobs.shared import io_utils


@pytest.fixture(scope="module")
def well_trajectory_arguments():
    return ["-c", "config.yml"]


def test_well_trajectory_simple_main_entry_point(
    well_trajectory_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
    main_entry_point(well_trajectory_arguments)

    for expected in Path("expected").glob("**/*"):
        if expected.is_file() and expected.name != "wells.json":
            output = expected.relative_to("expected")
            assert output.is_file()
            assert filecmp.cmp(expected, output, shallow=False)


def test_well_trajectory_with_simple_main_entry_point_wells_file(
    well_trajectory_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")

    config = io_utils.load_yaml("config.yml")
    config["wells_file"] = "wells.json"
    with Path("config.yml").open("w") as fp:
        io_utils.dump_yaml(config, fp)

    main_entry_point(well_trajectory_arguments)

    for expected in Path("expected").glob("**/*"):
        if expected.is_file():
            output = expected.relative_to("expected")
            assert output.is_file()
            assert filecmp.cmp(expected, output, shallow=False)


def test_well_trajectory_simple_main_entry_point_lint(
    well_trajectory_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
    with pytest.raises(SystemExit):
        main_entry_point([*well_trajectory_arguments, "--lint"])

    assert not any(
        path.relative_to("expected").exists()
        for path in Path("expected").glob("**/*")
        if path.name != "wells.json"
    )
