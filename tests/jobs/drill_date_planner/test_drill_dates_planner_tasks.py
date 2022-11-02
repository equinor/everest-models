import pytest
from sub_testdata import DRILL_DATE_PLANNER as TEST_DATA
from utils import MockParser

from spinningjenny.jobs.fm_drill_date_planner.tasks import drill_date_planner
from spinningjenny.jobs.utils.validators import valid_json_file


def test_drill_date_planner(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    parser = MockParser()
    wells = valid_json_file("wells.json", parser)
    controls = valid_json_file("controls.json", parser)
    output = drill_date_planner(wells, controls, [0.0, 1.0], 300)
    expected = valid_json_file("expected_result.json", parser)
    assert output == expected


def test_drill_date_planner_bounds_error(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    parser = MockParser()
    wells = valid_json_file("wells.json", parser)
    controls = valid_json_file("controls.json", parser)
    with pytest.raises(ValueError, match="Invalid bounds: \[1.0, 0.0\]"):
        drill_date_planner(wells, controls, [1.0, 0.0], 300)


def test_drill_date_planner_missing_well(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    parser = MockParser()
    wells = valid_json_file("wells.json", parser)
    controls = valid_json_file("controls.json", parser)
    del wells[1]
    with pytest.raises(RuntimeError, match="Drill time missing for well: WELL2"):
        drill_date_planner(wells, controls, [0.0, 0.1], 300)


def test_drill_date_planner_missing_control(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    parser = MockParser()
    wells = valid_json_file("wells.json", parser)
    controls = valid_json_file("controls.json", parser)
    del controls["WELL2"]
    with pytest.raises(RuntimeError, match="Missing well in controls: WELL2"):
        drill_date_planner(wells, controls, [0.0, 0.1], 300)
