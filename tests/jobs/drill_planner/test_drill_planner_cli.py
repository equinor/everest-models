import pathlib

import pytest
from sub_testdata import DRILL_PLANNER as TEST_DATA

from everest_models.jobs.fm_drill_planner.cli import main_entry_point
from everest_models.jobs.fm_drill_planner.manager import ScheduleError

OUTPUT_FILENAME = "out.json"


@pytest.fixture(scope="session")
def drill_planner_arguments():
    return [
        "--output",
        OUTPUT_FILENAME,
        "--optimizer",
        "optimizer_values.yml",
        "--config",
        "config.yml",
    ]


@pytest.mark.parametrize("wells_input", ["json", "config"])
def test_drill_planner_main_entry_point(
    drill_planner_arguments, copy_testdata_tmpdir, wells_input, add_wells_to_config
):
    copy_testdata_tmpdir(TEST_DATA)
    if wells_input == "json":
        args = (*drill_planner_arguments, "--input", "wells.json")
    else:
        args = drill_planner_arguments
        add_wells_to_config("wells.json", "config.yml")
    main_entry_point([*args])

    assert (
        pathlib.Path(OUTPUT_FILENAME).read_bytes()
        == pathlib.Path("correct_out.json").read_bytes()
    )


@pytest.mark.parametrize("wells_input", ["json", "config"])
def test_drill_planner_main_entry_point_partial_wells(
    drill_planner_arguments, copy_testdata_tmpdir, wells_input, add_wells_to_config
):
    copy_testdata_tmpdir(TEST_DATA)
    if wells_input == "json":
        args = (*drill_planner_arguments, "--input", "partial_wells.json")
    else:
        args = drill_planner_arguments
        add_wells_to_config("partial_wells.json", "config.yml")
    main_entry_point([*args])
    assert (
        pathlib.Path(OUTPUT_FILENAME).read_bytes()
        == pathlib.Path("partial_correct_out.json").read_bytes()
    )


@pytest.mark.parametrize("wells_input", ["json", "config"])
def test_drill_planner_main_entry_point_no_slots(
    drill_planner_arguments, copy_testdata_tmpdir, wells_input, add_wells_to_config
):
    copy_testdata_tmpdir(TEST_DATA)
    if wells_input == "json":
        args = ("--input", "wells.json", *drill_planner_arguments[:-1])
    else:
        args = drill_planner_arguments[:-1]
        add_wells_to_config("wells.json", "config_no_slots.yml")
    main_entry_point([*args, "config_no_slots.yml"])
    if wells_input == "json":
        args = (
            "--input",
            "wells.json",
            "--output",
            "out_single_slot.json",
            *drill_planner_arguments[2:-1],
        )
    else:
        args = ("--output", "out_single_slot.json", *drill_planner_arguments[2:-1])
        add_wells_to_config("wells.json", "config_single_slots.yml")
    main_entry_point([*args, "config_single_slots.yml"])

    assert (
        pathlib.Path(OUTPUT_FILENAME).read_bytes()
        == pathlib.Path("out_single_slot.json").read_bytes()
    )


@pytest.mark.parametrize("wells_input", ["json", "config"])
@pytest.mark.parametrize("config_argument", ("config.yml", "config_early_end_date.yml"))
def test_drill_planner_main_entry_point_ignore_end_date_no_effect(
    config_argument,
    drill_planner_arguments,
    copy_testdata_tmpdir,
    wells_input,
    add_wells_to_config,
):
    copy_testdata_tmpdir(TEST_DATA)
    if wells_input == "json":
        args = ("--input", "wells.json", *drill_planner_arguments[:-1])
    else:
        args = drill_planner_arguments[:-1]
        add_wells_to_config("wells.json", config_argument)
    main_entry_point([*args, config_argument, "--ignore-end-date"])

    assert (
        pathlib.Path(OUTPUT_FILENAME).read_bytes()
        == pathlib.Path("correct_out.json").read_bytes()
    )


@pytest.mark.parametrize("wells_input", ["json", "config"])
def test_drill_planner_main_entry_point_ignore_end_date(
    drill_planner_arguments, copy_testdata_tmpdir, wells_input, add_wells_to_config
):
    copy_testdata_tmpdir(TEST_DATA)
    if wells_input == "json":
        args = ("--input", "wells.json", *drill_planner_arguments[:-1])
    else:
        args = drill_planner_arguments[:-1]
        add_wells_to_config("wells.json", "config_early_end_date.yml")
    with pytest.raises(ScheduleError, match="is well drilled once"):
        main_entry_point([*args, "config_early_end_date.yml"])


@pytest.mark.parametrize("wells_input", ["json", "config"])
def test_drill_planner_main_entry_point_lint(
    drill_planner_arguments, copy_testdata_tmpdir, wells_input, add_wells_to_config
):
    copy_testdata_tmpdir(TEST_DATA)
    if wells_input == "json":
        args = ("--input", "wells.json", *drill_planner_arguments)
    else:
        args = drill_planner_arguments
        add_wells_to_config("wells.json", "config.yml")
    with pytest.raises(SystemExit):
        main_entry_point([*args, "--lint"])


def test_drill_planner_error_no_wells_in_input_or_config(
    copy_testdata_tmpdir, drill_planner_arguments, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as e:
        main_entry_point([*drill_planner_arguments])

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "either --input or config.wells must be provided!" in err


def test_drill_planner_error_both_wells_in_input_and_config(
    copy_testdata_tmpdir, drill_planner_arguments, add_wells_to_config, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    add_wells_to_config("wells.json", "config.yml")
    with pytest.raises(SystemExit) as e:
        main_entry_point([*drill_planner_arguments, "--input", "wells.json"])

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "--input and config.wells are mutually exclusive!" in err
