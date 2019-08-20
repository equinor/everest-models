from spinningjenny.script.fm_drill_planner import (
    main_entry_point as drill_planner_entry,
)
from spinningjenny.script.fm_well_constraints import (
    main_entry_point as well_constraints_entry,
)
from spinningjenny.script.fm_add_templates import (
    main_entry_point as add_templates_entry,
)
from spinningjenny.script.fm_schmerge import main_entry_point as schmerge_entry
from spinningjenny.script.fm_interpret_well_drill import (
    main_entry_point as interpret_entry,
)
from spinningjenny.script.fm_well_filter import main_entry_point as filter_entry

from tests import tmpdir, relpath

TEST_DATA_PATH = relpath("tests", "testdata", "workflows")


@tmpdir(TEST_DATA_PATH)
def test_workflow():

    arguments = [
        "-i",
        "interpreter_optimizer_values.yml",
        "-o",
        "filter_keep_wells.json",
    ]

    interpret_entry(arguments)

    arguments = [
        "-i",
        "wells.json",
        "--keep",
        "filter_keep_wells.json",
        "-o",
        "filtered_wells.json",
    ]

    filter_entry(arguments)

    arguments = [
        "-i",
        "filtered_wells.json",
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
        "--remove",
        "remove_EXTRA2.json",
        "-o",
        "filtered_wells_dp_result.json",
    ]

    filter_entry(arguments)

    arguments = [
        "-i",
        "filtered_wells_dp_result.json",
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
