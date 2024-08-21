import filecmp
import json
import logging
from pathlib import Path

import pytest
from sub_testdata import WELL_TRAJECTORY as TEST_DATA

from everest_models.jobs.fm_well_trajectory.cli import main_entry_point
from everest_models.jobs.fm_well_trajectory.well_trajectory_resinsight import ResInsight


@pytest.fixture(scope="module")
def well_trajectory_arguments():
    return ("-c config.yml -E SPE1CASE1_MLT").split()


@pytest.mark.slow
@pytest.mark.resinsight
def test_failing_start_resinsight(caplog):
    caplog.set_level(logging.INFO)
    with pytest.raises(
        ConnectionError,
        match="Failed to launch ResInsight executable: _non_existing_binary_",
    ), ResInsight("_non_existing_binary_"):
        pass
    assert "Launching ResInsight..." in caplog.text


@pytest.mark.resinsight
def test_start_resinsight(caplog):
    with ResInsight() as ri:
        assert ri.project.cases() == []
    assert "Launching ResInsight..." in caplog.text


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_lint(
    well_trajectory_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight_mlt")
    with pytest.raises(SystemExit):
        main_entry_point([*well_trajectory_arguments, "--lint"])

    assert not any(
        path.relative_to("expected").exists() for path in Path("expected").glob("**/*")
    )


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_no_mlt(
    well_trajectory_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight_mlt")
    for path in Path.cwd().glob("mlt_*.json"):
        path.unlink()
    main_entry_point(well_trajectory_arguments)

    for expected in Path("expected").glob("**/*"):
        if expected.is_file():
            output = expected.relative_to("expected")
            assert output.is_file()
            assert filecmp.cmp(expected, output, shallow=False)


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_mlt(
    well_trajectory_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight_mlt")
    main_entry_point(well_trajectory_arguments)

    for expected in Path("expected_mlt").glob("**/*"):
        if expected.is_file():
            output = expected.relative_to("expected_mlt")
            assert output.is_file()
            assert filecmp.cmp(expected, output, shallow=False)


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_mixed(
    well_trajectory_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight_mlt")
    for path in Path.cwd().glob("mlt_*.json"):
        with path.open(encoding="utf-8") as fp:
            guide_points = json.load(fp)
        del guide_points["PROD"]
        with path.open("w", encoding="utf-8") as fp:
            json.dump(guide_points, fp)
    main_entry_point(well_trajectory_arguments)

    for expected in Path("expected_mixed").glob("**/*"):
        if expected.is_file():
            output = expected.relative_to("expected_mixed")
            assert output.is_file()
            assert filecmp.cmp(expected, output, shallow=False)
