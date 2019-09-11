from __future__ import absolute_import
from spinningjenny.script.fm_extract_summary_data import main_entry_point
from spinningjenny.extract_summary_data import CalculationType

from tests import tmpdir, relpath
import os
import pytest

TEST_DATA_PATH = relpath("tests", "testdata", "stripdates")


@tmpdir(TEST_DATA_PATH)
def test_extract_summary_data_entry_point(caplog):
    output_file = "test_out"
    expected_results = {
        "max": 1848592.0,
        "mean": 506800.1167883212,
        "median": 514302.1176470518,
        "percentile": 1399374.5262230039,
        "cumulative": 555452928.0,
    }

    # check range calculations
    for calc_type in CalculationType.types():
        args = [
            "-s",
            "REEK-0.UNSMRY",
            "-sd",
            "2000-01-01",
            "-ed",
            "2003-01-01",
            "-t",
            calc_type,
            "-k",
            "FGPT",
            "-o",
            output_file,
        ]

        main_entry_point(args)
        assert os.path.exists(output_file)
        with open(output_file, "r") as f:
            result = float(f.readline())

        assert result == expected_results[calc_type]

    log_messages = [rec.message for rec in caplog.records]

    assert len(log_messages) == 0

    args = [
        "-s",
        "REEK-0.UNSMRY",
        "--date",
        "2001-04-01",
        "-t",
        "median",
        "-k",
        "FGPT",
        "-o",
        output_file,
    ]
    main_entry_point(args)
    assert os.path.exists(output_file)
    with open(output_file, "r") as f:
        result = float(f.readline())
    expected_result = 1157883.875
    assert result == expected_result

    log_messages = [rec.message for rec in caplog.records]

    assert "Cannot perform range calculation on a single date!" in log_messages


@tmpdir(TEST_DATA_PATH)
def test_percentile_calculation(capsys):
    output_file = "test_out"
    expected_result = 13529.59375
    args = [
        "-s",
        "REEK-0.UNSMRY",
        "-sd",
        "2000-01-01",
        "-ed",
        "2003-01-01",
        "-t",
        "percentile",
        "-p",
        "42xxxx",
        "-k",
        "FGPT",
        "-o",
        output_file,
    ]

    with pytest.raises(SystemExit) as e:
        main_entry_point(args)

    assert e.value.code == 2
    _, err = capsys.readouterr()

    assert "Invalid percentile value provided '42xxxx'" in err

    args = [
        "-s",
        "REEK-0.UNSMRY",
        "-sd",
        "2000-01-01",
        "-ed",
        "2003-01-01",
        "-t",
        "percentile",
        "-p",
        "42",
        "-k",
        "FGPT",
        "-o",
        output_file,
    ]

    main_entry_point(args)
    assert os.path.exists(output_file)
    with open(output_file, "r") as f:
        result = float(f.readline())

    assert result == expected_result
