import os
from pathlib import Path

import pytest
from jobs.extract_summary_data.parser import build_argument_parser

from everest_models.jobs.fm_extract_summary_data import cli
from everest_models.jobs.fm_extract_summary_data.tasks import CalculationType


@pytest.fixture()
def mock_extract_summary_data_parser(monkeypatch):
    monkeypatch.setattr(
        cli,
        "args_parser",
        build_argument_parser(),
    )


@pytest.fixture(scope="module")
def extract_summary_data_base_args():
    return (
        "--summary",
        "PATCHED.UNSMRY",
        "--output",
        "test_out",
        "--key",
        "FGPT",
    )


@pytest.fixture(scope="module", params=CalculationType.types())
def extract_summary_data_args_types(extract_summary_data_base_args, request):
    selection_args = (
        ("--diff",) if request.param == "diff" else ("--aggregation", request.param)
    )
    return (
        *extract_summary_data_base_args,
        "--start-date",
        "2000-01-01",
        "--end-date",
        "2000-01-26",
        *selection_args,
    )


def test_extract_summary_data_entry_point(
    extract_summary_data_args_types,
    mock_extract_summary_data_parser,
    switch_cwd_tmp_path,
):
    output_file = extract_summary_data_args_types[3]
    expected_results = {"max": 10, "min": 2, "mean": 6, "median": 6, "diff": 8}
    # check range calculations
    cli.main_entry_point(extract_summary_data_args_types)
    with open(output_file) as f:
        result = float(f.readline())

    selection = (
        "diff"
        if "--diff" in extract_summary_data_args_types
        else extract_summary_data_args_types[-1]
    )
    assert result == expected_results[selection]


def test_extract_summary_data_lint(
    extract_summary_data_args_types,
    switch_cwd_tmp_path,
    mock_extract_summary_data_parser,
):
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point([*extract_summary_data_args_types, "--lint"])

    assert e.value.code == 0
    assert not Path("output.json").exists()


def test_extract_summary_data_entry_point_default_type_uses_last_value(
    extract_summary_data_base_args,
    mock_extract_summary_data_parser,
    switch_cwd_tmp_path,
):
    output_file = extract_summary_data_base_args[3]
    cli.main_entry_point(
        [
            *extract_summary_data_base_args,
            "--start-date",
            "2000-01-01",
            "--end-date",
            "2000-01-26",
        ]
    )
    with open(output_file) as f:
        result = float(f.readline())

    assert result == 10


def test_extract_summary_data_entry_point_single_date(
    extract_summary_data_base_args,
    caplog,
    mock_extract_summary_data_parser,
    switch_cwd_tmp_path,
):
    output_file = extract_summary_data_base_args[3]
    cli.main_entry_point(
        [
            *extract_summary_data_base_args,
            "--date",
            "2000-01-21",
        ]
    )
    assert os.path.exists(output_file)
    with open(output_file) as f:
        result = float(f.readline())
    expected_result = 8
    assert result == expected_result

    log_messages = [rec.message for rec in caplog.records]

    assert "Extracting key FGPT for single date 2000-01-21" in log_messages


def test_extract_summary_data_entry_point_defaults_to_last_date(
    extract_summary_data_base_args,
    mock_extract_summary_data_parser,
    switch_cwd_tmp_path,
):
    output_file = extract_summary_data_base_args[3]
    cli.main_entry_point(extract_summary_data_base_args)

    with open(output_file) as f:
        result = float(f.readline())

    assert result == 10


def test_extract_summary_data_applies_unit_conversion(
    extract_summary_data_base_args,
    mock_extract_summary_data_parser,
    switch_cwd_tmp_path,
):
    output_file = extract_summary_data_base_args[3]
    cli.main_entry_point(
        [
            *extract_summary_data_base_args,
            "--date",
            "2000-01-21",
            "--unit-conversion",
            "2",
        ]
    )

    with open(output_file) as f:
        result = float(f.readline())

    assert result == 4


def test_extract_summary_data_rejects_zero_unit_conversion(
    extract_summary_data_base_args,
    mock_extract_summary_data_parser,
    switch_cwd_tmp_path,
):
    with pytest.raises(SystemExit):
        cli.main_entry_point(
            [*extract_summary_data_base_args, "--unit-conversion", "0"]
        )
