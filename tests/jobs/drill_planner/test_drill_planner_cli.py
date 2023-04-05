import pathlib

import pytest
from sub_testdata import DRILL_PLANNER as TEST_DATA

from spinningjenny.jobs.fm_drill_planner.cli import main_entry_point
from spinningjenny.jobs.fm_drill_planner.manager import ScheduleError

OUTPUT_FILENAME = "out.json"


@pytest.fixture(scope="session")
def drill_planner_arguments():
    return [
        "--output",
        OUTPUT_FILENAME,
        "--optimizer",
        "optimizer_values.yml",
        "--input",
        "wells.json",
        "--config",
        "config.yml",
    ]


def test_drill_planner_main_entry_point(drill_planner_arguments, copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    main_entry_point(drill_planner_arguments)

    assert (
        pathlib.Path(OUTPUT_FILENAME).read_bytes()
        == pathlib.Path("correct_out.json").read_bytes()
    )


def test_drill_planner_main_entry_point_partial_wells(
    drill_planner_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)
    main_entry_point(
        [
            *drill_planner_arguments[:-3],
            "partial_wells.json",
            *drill_planner_arguments[-2:],
        ]
    )
    assert (
        pathlib.Path(OUTPUT_FILENAME).read_bytes()
        == pathlib.Path("partial_correct_out.json").read_bytes()
    )


def test_drill_planner_main_entry_point_no_slots(
    drill_planner_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)
    main_entry_point([*drill_planner_arguments[:-1], "config_no_slots.yml"])
    main_entry_point(
        [
            "--output",
            "out_single_slot.json",
            *drill_planner_arguments[2:-1],
            "config_single_slots.yml",
        ]
    )

    assert (
        pathlib.Path(OUTPUT_FILENAME).read_bytes()
        == pathlib.Path("out_single_slot.json").read_bytes()
    )


@pytest.mark.parametrize("config_argument", ("config.yml", "config_early_end_date.yml"))
def test_drill_planner_main_entry_point_ignore_end_date_no_effect(
    config_argument, drill_planner_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)
    main_entry_point(
        [*drill_planner_arguments[:-1], config_argument, "--ignore-end-date"]
    )

    assert (
        pathlib.Path(OUTPUT_FILENAME).read_bytes()
        == pathlib.Path("correct_out.json").read_bytes()
    )


def test_drill_planner_main_entry_point_ignore_end_date(
    drill_planner_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(ScheduleError, match="is well drilled once"):
        main_entry_point([*drill_planner_arguments[:-1], "config_early_end_date.yml"])


def test_drill_planner_main_entry_point_lint(
    drill_planner_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as e:
        main_entry_point([*drill_planner_arguments, "--lint"])
