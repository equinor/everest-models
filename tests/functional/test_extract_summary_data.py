from __future__ import absolute_import

from spinningjenny.script import fm_extract_summary_data
from spinningjenny.script.fm_extract_summary_data import main_entry_point
from spinningjenny.extract_summary_data import CalculationType

from tests import tmp
from tests.summary import ecl_summary

import os


def test_extract_summary_data_entry_point(monkeypatch, caplog):
    output_file = "test_out"
    expected_results = {"max": 10, "diff": 8}
    monkeypatch.setattr(
        fm_extract_summary_data, "valid_ecl_file", ecl_summary,
    )
    # check range calculations
    for calc_type in CalculationType.types():
        args = [
            "-s",
            "PATCHED.UNSMRY",
            "-sd",
            "2000-01-01",
            "-ed",
            "2000-01-26",
            "-t",
            calc_type,
            "-k",
            "FGPT",
            "-o",
            output_file,
        ]
        with tmp():
            main_entry_point(args)
            assert os.path.exists(output_file)
            with open(output_file, "r") as f:
                result = float(f.readline())

        assert result == expected_results[calc_type]

    log_messages = [rec.message for rec in caplog.records]

    assert len(log_messages) == 0

    for calc_type in CalculationType.types():
        args = [
            "-s",
            "PATCHED.UNSMRY",
            "-sd",
            "2000-01-01",
            "-ed",
            "2000-01-26",
            "-t",
            calc_type,
            "-k",
            "FGPT",
            "-m",
            "2.6",
            "-o",
            output_file,
        ]

        with tmp():
            main_entry_point(args)
            assert os.path.exists(output_file)
            with open(output_file, "r") as f:
                result = float(f.readline())

        assert result == 2.6 * expected_results[calc_type]

    log_messages = [rec.message for rec in caplog.records]

    assert len(log_messages) == 0

    args = [
        "-s",
        "PATCHED.UNSMRY",
        "--date",
        "2000-01-21",
        "-k",
        "FGPT",
        "-o",
        output_file,
    ]
    with tmp():
        main_entry_point(args)
        assert os.path.exists(output_file)
        with open(output_file, "r") as f:
            result = float(f.readline())
    expected_result = 8
    assert result == expected_result

    log_messages = [rec.message for rec in caplog.records]

    assert "Extracting key FGPT for single date 2000-01-21" in log_messages
