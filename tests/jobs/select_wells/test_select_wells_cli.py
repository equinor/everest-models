import pytest
from sub_testdata import SELECT_WELLS as TEST_DATA

from spinningjenny.jobs.fm_select_wells.cli import main_entry_point
from spinningjenny.jobs.shared.io_utils import load_yaml


def test_select_wells_main_entry_point(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = (
        "--input input.json --well-number-file well_number.json"
        " --scaled-bounds 0.0 1.0 --real-bounds 0 47 --output output.json"
    ).split()
    main_entry_point(arguments)
    test_output = load_yaml("output.json")
    expected_output = load_yaml("expected_result.json")
    assert test_output == expected_output


def test_select_wells_main_entry_point_no_input(copy_testdata_tmpdir, capsys):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = ("--input input.json --output output.json").split()
    with pytest.raises(SystemExit) as exc:
        main_entry_point(arguments)
        assert exc.value.code == 2
    captured = capsys.readouterr()
    msg = (
        "-n/--well-number and -f/--well-number-file are both missing:"
        " -m/--max-date is required"
    )
    assert captured.err.find(msg) >= 0


def test_select_wells_main_entry_point_with_date(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = (
        "--input input.json --well-number 100 --max-date 2023-03-01 --output output.json"
    ).split()
    main_entry_point(arguments)
    test_output = load_yaml("output.json")
    expected_output = load_yaml("expected_result.json")
    assert test_output == expected_output


def test_select_wells_main_entry_point_with_date_none(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = (
        "--input input.json --max-date 2023-03-01 --output output.json"
    ).split()
    main_entry_point(arguments)
    test_output = load_yaml("output.json")
    expected_output = load_yaml("expected_result.json")
    assert test_output == expected_output


def test_select_wells_main_entry_point_n(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = ("--input input.json --well-number 2 --output output.json").split()
    main_entry_point(arguments)
    test_output = load_yaml("output.json")
    expected_output = load_yaml("expected_result.json")
    assert test_output == expected_output


def test_select_wells_main_entry_point_n_gt_0(copy_testdata_tmpdir, capsys):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = ("--input input.json --well-number -1 --output output.json").split()
    with pytest.raises(SystemExit) as exc:
        main_entry_point(arguments)
        assert exc.value.code == 2
    captured = capsys.readouterr()
    msg = "-n/--well-number must be > 0"
    assert captured.err.find(msg) >= 0


def test_select_wells_main_entry_point_n_bounds(copy_testdata_tmpdir, capsys):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = (
        "--input input.json --well-number 2 --output output.json"
        " --scaled-bounds 0.0 1.0"
    ).split()
    with pytest.raises(SystemExit) as exc:
        main_entry_point(arguments)
        assert exc.value.code == 2
    captured = capsys.readouterr()
    msg = "Scaling bounds are not allowed if -n/--well-number is given"
    assert captured.err.find(msg) >= 0


def test_select_wells_main_entry_point_no_bounds(copy_testdata_tmpdir, capsys):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = (
        "--input input.json --well-number-file well_number.json"
        " --scaled-bounds 0.0 1.0 --output output.json"
    ).split()
    with pytest.raises(SystemExit) as exc:
        main_entry_point(arguments)
        assert exc.value.code == 2


def test_select_wells_main_entry_point_file_and_number(copy_testdata_tmpdir, capsys):
    copy_testdata_tmpdir(TEST_DATA)
    arguments = (
        "--input input.json --well-number-file well_number.json"
        " --well-number 2 --output output.json"
    ).split()
    with pytest.raises(SystemExit) as exc:
        main_entry_point(arguments)
        assert exc.value.code == 2
    captured = capsys.readouterr()
    msg = "argument -n/--well-number: not allowed with argument -f/--well-number-file"
    assert captured.err.find(msg) >= 0
