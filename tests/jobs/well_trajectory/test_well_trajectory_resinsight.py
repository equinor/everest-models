import logging
from pathlib import Path

import pytest
from everest_models.jobs.fm_well_trajectory.cli import main_entry_point
from everest_models.jobs.fm_well_trajectory.well_trajectory_resinsight import ResInsight
from sub_testdata import WELL_TRAJECTORY as TEST_DATA


@pytest.fixture(scope="module")
def well_trajectory_arguments():
    return ("-c config.yml -E SPE1CASE1").split()


@pytest.fixture(scope="module")
def well_trajectory_output_files():
    return (
        "well_geometry.txt",
        "wellpaths/INJ.dev",
        "wellpaths/PROD.dev",
        "INJ.SCH",
        "PROD.SCH",
        "guide_points.json",
    )


@pytest.mark.resinsight
def test_failing_start_resinsight(caplog):
    caplog.set_level(logging.INFO)
    with pytest.raises(
        ConnectionError,
        match="Failed to launch ResInsight executable: _non_existing_binary_",
    ):
        with ResInsight("_non_existing_binary_"):
            pass
    assert "Launching ResInsight..." in caplog.text


@pytest.mark.resinsight
def test_start_resinsight(caplog):
    with ResInsight() as ri:
        assert ri.project.cases() == []
    assert "Launching ResInsight..." in caplog.text


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point(
    well_trajectory_arguments, well_trajectory_output_files, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "spe1case1")
    main_entry_point(well_trajectory_arguments)
    assert all(
        path.read_bytes() == (Path("expected") / path).read_bytes()
        for path in map(Path, well_trajectory_output_files)
    )


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_lint(
    well_trajectory_arguments, well_trajectory_output_files, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "spe1case1")
    with pytest.raises(SystemExit):
        main_entry_point([*well_trajectory_arguments, "--lint"])

    assert not any(path.exists() for path in map(Path, well_trajectory_output_files))
