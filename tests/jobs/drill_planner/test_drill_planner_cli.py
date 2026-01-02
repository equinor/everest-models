import json
import pathlib

import pytest
import yaml
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


@pytest.mark.usefixtures("switch_cwd_tmp_path")
def test_drill_planner_main_entry_point_not_enough_slots():
    """If there are more wells than slots, the schedule produced will be erroneous.

    The schedule will fail two validators, as there are wells in it that
    are not drilled at least once, and also the more general validator
    that there must be at least as many slots as wells.
    """
    pathlib.Path("wells.json").write_text(
        json.dumps(
            [{"name": "w1", "drill_time": 1}, {"name": "w2", "drill_time": 1}],
        ),
        encoding="utf-8",
    )
    pathlib.Path("opt.yml").write_text("w1: 1\nw2: 2", encoding="utf-8")
    pathlib.Path("config.yml").write_text(
        yaml.dump(
            {
                "start_date": "2000-01-01",
                "rigs": [{"name": "A", "wells": ["w1", "w2"], "slots": ["s1"]}],
                "slots": [{"name": "s1", "wells": ["w1", "w2"]}],  # only one slot here
            }
        )
    )
    with pytest.raises(ScheduleError, match="enough slots"):
        main_entry_point(
            [
                "--output",
                "foo.json",
                "--optimizer",
                "opt.yml",
                "--input",
                "wells.json",
                "--config",
                "config.yml",
            ]
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
    with pytest.raises(SystemExit):
        main_entry_point([*drill_planner_arguments, "--lint"])
