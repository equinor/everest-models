import pytest

from spinningjenny import valid_json_file
from spinningjenny.drill_date_planner_job import drill_date_planner
from tests import MockParser, relpath, tmpdir

TEST_DATA_PATH = relpath("tests", "testdata", "drill_date_planner")


@tmpdir(TEST_DATA_PATH)
def test_drill_date_planner():
    parser = MockParser()
    wells = valid_json_file("wells.json", parser)
    controls = valid_json_file("controls.json", parser)
    output = drill_date_planner(wells, controls, [0.0, 1.0], 300)
    expected = valid_json_file("expected_result.json", parser)
    assert output == expected


@tmpdir(TEST_DATA_PATH)
def test_drill_date_planner_bounds_error():
    parser = MockParser()
    wells = valid_json_file("wells.json", parser)
    controls = valid_json_file("controls.json", parser)
    with pytest.raises(ValueError, match="Invalid bounds: \[1.0, 0.0\]"):
        drill_date_planner(wells, controls, [1.0, 0.0], 300)


@tmpdir(TEST_DATA_PATH)
def test_drill_date_planner_missing_well():
    parser = MockParser()
    wells = valid_json_file("wells.json", parser)
    controls = valid_json_file("controls.json", parser)
    del wells[1]
    with pytest.raises(RuntimeError, match="Drill time missing for well: WELL2"):
        drill_date_planner(wells, controls, [0.0, 0.1], 300)


@tmpdir(TEST_DATA_PATH)
def test_drill_date_planner_missing_control():
    parser = MockParser()
    wells = valid_json_file("wells.json", parser)
    controls = valid_json_file("controls.json", parser)
    del controls["WELL2"]
    with pytest.raises(RuntimeError, match="Missing well in controls: WELL2"):
        drill_date_planner(wells, controls, [0.0, 0.1], 300)
