import datetime
import logging
import pathlib

import pytest
from resdata.summary import Summary

from everest_models.jobs.fm_rf import cli
from everest_models.jobs.fm_rf.parser import args_parser

ARGUMENTS = ["-s", "TEST", "-o", "rf_result"]

RANGE_SIZE = 10 + 1


@pytest.fixture(scope="module")
def ecl_summary_rf():
    ecl_sum = Summary.writer("TEST", datetime.date(2000, 1, 1), *[RANGE_SIZE - 1] * 3)
    sum_keys = {
        "FOPT": list(range(RANGE_SIZE)),
        "FOIP": [100] * RANGE_SIZE,
        "GOPT:G1": [i / 2.0 for i in range(RANGE_SIZE)],
        "ROIP:1": [50] * RANGE_SIZE,
    }

    for key in sum_keys:
        name, sub_name = key.split(":") if ":" in key else (key, None)
        num, wgname = (
            (int(sub_name), None)
            if sub_name and sub_name.isnumeric()
            else (0, sub_name)
        )
        ecl_sum.add_variable(name, wgname=wgname, num=num)

    for index in range(RANGE_SIZE):
        t_step = ecl_sum.add_t_step(index, index)
        for key, item in sum_keys.items():
            t_step[key] = item[index]

    return ecl_sum


@pytest.fixture
def mock_rf_parser(ecl_summary_rf, monkeypatch):
    def build_argument_parser():
        parser = args_parser
        parser._actions[1].type = lambda *x, **y: ecl_summary_rf
        return parser

    monkeypatch.setattr(
        cli,
        "args_parser",
        build_argument_parser(),
    )


@pytest.mark.parametrize(
    "more_args, expected",
    (
        pytest.param((), b"0.100000", id="required only"),
        pytest.param(
            (
                "-pk",
                "GOPT:G1",
            ),
            b"0.050000",
            id="production key",
        ),
        pytest.param(
            (
                "-ed",
                "2000-01-06",
            ),
            b"0.050000",
            id="end date",
        ),
        pytest.param(
            (
                "-sd",
                "2000-01-03",
                "-ed",
                "2000-01-07",
            ),
            b"0.040000",
            id="start and end date",
        ),
        pytest.param(
            (
                "-pk",
                "GOPT:G1",
                "-sd",
                "2000-01-03",
                "-ed",
                "2000-01-07",
            ),
            b"0.020000",
            id="production key and dates",
        ),
        pytest.param(
            (
                "-pk",
                "GOPT:G1",
                "-tvk",
                "ROIP:1",
                "-sd",
                "2000-01-03",
                "-ed",
                "2000-01-07",
            ),
            b"0.040000",
            id="all arguments",
        ),
    ),
)
def test_rf_entry_point(more_args, expected, switch_cwd_tmp_path, mock_rf_parser):
    cli.main_entry_point((*ARGUMENTS, *more_args))
    assert pathlib.Path("rf_result").read_bytes() == expected


@pytest.mark.parametrize(
    "args, expected, log",
    (
        pytest.param(
            ("-sd", "1999-01-01", "-ed", "2000-01-06"),
            b"0.050000",
            "The date range 1999-01-01 - 2000-01-06 exceeds the simulation time, "
            "clamping to simulation time: 2000-01-01 - 2000-01-11",
            id="end and start date",
        ),
        pytest.param(
            ("-ed", "2001-01-01"),
            b"0.100000",
            "The date range 2000-01-01 - 2001-01-01 exceeds the simulation time, "
            "clamping to simulation time: 2000-01-01 - 2000-01-11",
            id="end date",
        ),
    ),
)
def test_rf_entry_point_date_out_of_simulation_bounds(
    args, expected, log, switch_cwd_tmp_path, mock_rf_parser, caplog
):
    with caplog.at_level(logging.WARNING):
        cli.main_entry_point((*ARGUMENTS, *args))
    assert log in caplog.text
    assert pathlib.Path("rf_result").read_bytes() == expected


def test_rf_lint(
    switch_cwd_tmp_path,
    mock_rf_parser,
):
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point([*ARGUMENTS, "--lint"])

    assert e.value.code == 0
    assert not pathlib.Path("rf_result").exists()
