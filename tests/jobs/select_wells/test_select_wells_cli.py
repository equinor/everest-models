import pytest
from utils import relpath, tmpdir

from jobs.fm_select_wells.cli import main_entry_point
from jobs.utils.io_utils import load_yaml

TEST_DATA_PATH = relpath("tests", "testdata", "select_wells")


@tmpdir(TEST_DATA_PATH)
def test_select_wells_main_entry_point():
    arguments = (
        "--input input.json --well-number-file well_number.json"
        " --scaled-bounds 0.0 1.0 --real-bounds 0 47 --output output.json"
    ).split()
    main_entry_point(arguments)
    test_output = load_yaml("output.json")
    expected_output = load_yaml("expected_result.json")
    assert test_output == expected_output


@tmpdir(TEST_DATA_PATH)
def test_select_wells_main_entry_point_no_input(capsys):
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


@tmpdir(TEST_DATA_PATH)
def test_select_wells_main_entry_point_with_date():
    arguments = (
        "--input input.json --well-number 100 --max-date 2023-03-01 --output output.json"
    ).split()
    main_entry_point(arguments)
    test_output = load_yaml("output.json")
    expected_output = load_yaml("expected_result.json")
    assert test_output == expected_output


@tmpdir(TEST_DATA_PATH)
def test_select_wells_main_entry_point_with_date_none():
    arguments = (
        "--input input.json --max-date 2023-03-01 --output output.json"
    ).split()
    main_entry_point(arguments)
    test_output = load_yaml("output.json")
    expected_output = load_yaml("expected_result.json")
    assert test_output == expected_output


@tmpdir(TEST_DATA_PATH)
def test_select_wells_main_entry_point_n():
    arguments = ("--input input.json --well-number 2 --output output.json").split()
    main_entry_point(arguments)
    test_output = load_yaml("output.json")
    expected_output = load_yaml("expected_result.json")
    assert test_output == expected_output


@tmpdir(TEST_DATA_PATH)
def test_select_wells_main_entry_point_n_gt_0(capsys):
    arguments = ("--input input.json --well-number -1 --output output.json").split()
    with pytest.raises(SystemExit) as exc:
        main_entry_point(arguments)
        assert exc.value.code == 2
    captured = capsys.readouterr()
    msg = "-n/--well-number must be > 0"
    assert captured.err.find(msg) >= 0


@tmpdir(TEST_DATA_PATH)
def test_select_wells_main_entry_point_n_bounds(capsys):
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


@tmpdir(TEST_DATA_PATH)
def test_select_wells_main_entry_point_no_bounds(capsys):
    arguments = (
        "--input input.json --well-number-file well_number.json"
        " --scaled-bounds 0.0 1.0 --output output.json"
    ).split()
    with pytest.raises(SystemExit) as exc:
        main_entry_point(arguments)
        assert exc.value.code == 2


@tmpdir(TEST_DATA_PATH)
def test_select_wells_main_entry_point_file_and_number(capsys):
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
