from spinningjenny.script.drill_planner import main_entry_point as drill_planner_entry
from spinningjenny.script.well_constraints import (
    main_entry_point as well_constraints_entry,
)
from spinningjenny.script.add_templates import main_entry_point as add_templates_entry
from spinningjenny.script.schmerge import main_entry_point as schmerge_entry

from tests import tmpdir, relpath

TEST_DATA_PATH = relpath("tests", "testdata", "workflows")


@tmpdir(TEST_DATA_PATH)
def test_workflow():

    arguments = [
        "-i",
        "wells.json",
        "-c",
        "drill_planner_config.yml",
        "-opt",
        "optimizer_values.yml",
        "-o",
        "wells_dp_result.json",
    ]

    drill_planner_entry(arguments)

    arguments = [
        "-i",
        "wells_dp_result.json",
        "-c",
        "well_constraint_config.yml",
        "-rc",
        "rate_input.json",
        "-pc",
        "phase_input.json",
        "-dc",
        "duration_input.json",
        "-o",
        "wells_wc_result.json",
    ]

    well_constraints_entry(arguments)

    arguments = [
        "-c",
        "template_config.yml",
        "-i",
        "wells_wc_result.json",
        "-o",
        "wells_tmpl_result.json",
    ]

    add_templates_entry(arguments)

    arguments = [
        "-i",
        "raw_schedule.sch",
        "-c",
        "wells_tmpl_result.json",
        "-o",
        "result_schedule.sch",
    ]

    schmerge_entry(arguments)

    with open("result_schedule.sch") as f:
        test_output = f.read()

    with open("expected_schedule.sch") as f:
        expected_output = f.read()

    assert test_output == expected_output