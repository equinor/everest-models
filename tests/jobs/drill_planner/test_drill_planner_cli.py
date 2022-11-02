import pytest
from sub_testdata import DRILL_PLANNER as TEST_DATA

from spinningjenny.jobs.fm_drill_planner.cli import main_entry_point
from spinningjenny.jobs.utils.io_utils import load_yaml


def test_main_entry_point(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = [
        "--input",
        "wells.json",
        "--config",
        "config.yml",
        "--optimizer",
        "optimizer_values.yml",
        "--output",
        "out.json",
    ]

    main_entry_point(arguments)

    test_output = load_yaml("out.json")
    expected_output = load_yaml("correct_out.json")

    assert test_output == expected_output


def test_main_entry_point_partial_wells(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = [
        "--input",
        "partial_wells.json",
        "--config",
        "config.yml",
        "--optimizer",
        "optimizer_values.yml",
        "--output",
        "partial_out.json",
    ]

    main_entry_point(arguments)
    test_output = load_yaml("partial_out.json")
    expected_output = load_yaml("partial_correct_out.json")

    assert test_output == expected_output


def test_main_entry_point_no_slots(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = [
        "--input",
        "wells.json",
        "--config",
        "config_no_slots.yml",
        "--optimizer",
        "optimizer_values.yml",
        "--output",
        "out_no_slots.json",
    ]

    main_entry_point(arguments)

    arguments = [
        "--input",
        "wells.json",
        "--config",
        "config_single_slots.yml",
        "--optimizer",
        "optimizer_values.yml",
        "--output",
        "out_single_slots.json",
    ]

    main_entry_point(arguments)

    test_output = load_yaml("out_no_slots.json")
    expected_output = load_yaml("out_single_slots.json")

    assert test_output == expected_output


def test_main_entry_point_ignore_end_date_no_effect(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = [
        "--input",
        "wells.json",
        "--config",
        "config.yml",
        "--optimizer",
        "optimizer_values.yml",
        "--output",
        "out.json",
        "--ignore-end-date",
    ]

    main_entry_point(arguments)

    test_output = load_yaml("out.json")
    expected_output = load_yaml("correct_out.json")

    assert test_output == expected_output


def test_main_entry_point_ignore_end_date(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = [
        "--input",
        "wells.json",
        "--config",
        "config_early_end_date.yml",
        "--optimizer",
        "optimizer_values.yml",
        "--output",
        "out.json",
    ]

    with pytest.raises(RuntimeError):
        main_entry_point(arguments)

    arguments.append("--ignore-end-date")

    main_entry_point(arguments)

    test_output = load_yaml("out.json")
    expected_output = load_yaml("correct_out.json")

    assert test_output == expected_output
