import pathlib

import pytest
from sub_testdata import SELECT_WELLS as TEST_DATA

from everest_models.jobs.fm_select_wells.cli import main_entry_point


@pytest.fixture(scope="module")
def select_wells_base_args():
    return (
        "--input",
        "input.json",
        "--output",
        "output.json",
    )


@pytest.fixture(scope="module")
def select_wells_file_args():
    return (
        "file",
        "well_number.json",
        "--scaled-bounds",
        "0.0",
        "1.0",
        "--real-bounds",
        "0",
        "47",
    )


def test_select_wells_main_entry_point(
    copy_testdata_tmpdir, select_wells_base_args, select_wells_file_args
):
    copy_testdata_tmpdir(TEST_DATA)
    main_entry_point(
        [
            *select_wells_base_args,
            "--max-date",
            "2022-12-01",
            *select_wells_file_args,
        ]
    )
    assert (
        pathlib.Path("output.json").read_bytes()
        == b"""[
  {
    "completion_date": "2022-12-01",
    "drill_time": 50,
    "name": "WELL1",
    "ops": [
      {
        "date": "2022-12-01",
        "opname": "open"
      }
    ],
    "readydate": "2022-12-01"
  }
]"""
    )


def test_select_wells_main_entry_point_file_no_max_date(
    copy_testdata_tmpdir, select_wells_base_args, select_wells_file_args
):
    copy_testdata_tmpdir(TEST_DATA)
    main_entry_point(
        [
            *select_wells_base_args,
            *select_wells_file_args,
        ]
    )
    assert (
        pathlib.Path("output.json").read_bytes()
        == pathlib.Path("expected_result.json").read_bytes()
    )


def test_select_wells_main_entry_point_no_well_number_nor_max_date(
    copy_testdata_tmpdir, select_wells_base_args, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as exc:
        main_entry_point(
            select_wells_base_args,
        )

    assert exc.value.code == 2
    _, err = capsys.readouterr()
    assert (
        "\nBoth `well number` and `-m/--max-date` values are missing.\n"
        "Please provide either/or both values"
    ) in err


def test_select_wells_main_entry_point_with_date(
    copy_testdata_tmpdir, select_wells_base_args
):
    copy_testdata_tmpdir(TEST_DATA)
    main_entry_point(
        [*select_wells_base_args, "--max-date", "2023-03-01", "value", "100"]
    )
    assert (
        pathlib.Path("output.json").read_bytes()
        == pathlib.Path("expected_result.json").read_bytes()
    )


def test_select_wells_main_entry_point_well_number_as_value(
    copy_testdata_tmpdir, select_wells_base_args
):
    copy_testdata_tmpdir(TEST_DATA)
    main_entry_point([*select_wells_base_args, "value", "2"])
    assert (
        pathlib.Path("output.json").read_bytes()
        == pathlib.Path("expected_result.json").read_bytes()
    )


def test_select_wells_main_entry_point_value_not_gt_0(
    copy_testdata_tmpdir, select_wells_base_args, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as exc:
        main_entry_point([*select_wells_base_args, "value", "-1"])
    assert exc.value.code == 2
    _, err = capsys.readouterr()
    assert "well number must be > 0" in err


def test_select_wells_main_entry_point_value_with_scaled_bounds(
    copy_testdata_tmpdir, select_wells_base_args, select_wells_file_args, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as exc:
        main_entry_point(
            [*select_wells_base_args, "value", "2", *select_wells_file_args[2:]]
        )
    assert exc.value.code == 2
    _, err = capsys.readouterr()
    assert "unrecognized arguments: --scaled-bounds 0.0 1.0" in err


def test_select_wells_main_entry_point_no_real_bounds(
    copy_testdata_tmpdir, select_wells_base_args, select_wells_file_args, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as exc:
        main_entry_point([*select_wells_base_args, *select_wells_file_args[:-3]])
    assert exc.value.code == 2
    _, err = capsys.readouterr()
    assert "the following arguments are required: -r/--real-bounds" in err


def test_select_wells_main_entry_point_no_scaled_bounds(
    copy_testdata_tmpdir, select_wells_base_args, select_wells_file_args, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as exc:
        main_entry_point(
            [
                *select_wells_base_args,
                *select_wells_file_args[:2],
                *select_wells_file_args[5:],
            ]
        )
    assert exc.value.code == 2
    _, err = capsys.readouterr()
    assert "the following arguments are required: -s/--scaled-bounds" in err


def test_select_wells_lint(select_wells_base_args, copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as e:
        main_entry_point([*select_wells_base_args, "--lint", "value", "2"])

    assert e.value.code == 0
    assert not pathlib.Path("output.json").exists()
