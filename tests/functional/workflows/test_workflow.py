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
        "--input-file",
        "wells.json",
        "--config-file",
        "drill_planner_config.yml",
        "--optimizer-file",
        "optimizer_values.yml",
        "--output-file",
        "wells_dp_result.json",
    ]

    drill_planner_entry(arguments)

    arguments = [
        "prog",
        "--well-order-file",
        "wells_dp_result.json",
        "--user-config",
        "well_constraint_config.yml",
        "--rate-constraint",
        "rate_input.json",
        "--phase-constraint",
        "phase_input.json",
        "--duration-constraints",
        "duration_input.json",
        "--output-file",
        "wells_wc_result.json",
    ]

    well_constraints_entry(arguments)

    arguments = [
        "--config",
        "template_config.yml",
        "--input-file",
        "wells_wc_result.json",
        "--output-file",
        "wells_tmpl_result.json",
    ]

    add_templates_entry(arguments)

    arguments = [
        "schmerge",
        "--schedule-input",
        "raw_schedule.sch",
        "--config",
        "wells_tmpl_result.json",
        "--schedule-output",
        "result_schedule.sch",
    ]

    schmerge_entry(arguments)

    with open("result_schedule.sch") as f:
        test_output = f.read()

    with open("expected_schedule.sch") as f:
        expected_output = f.read()

    assert test_output == expected_output
