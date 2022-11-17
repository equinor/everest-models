from ecl.summary import EclSum
from utils import MockParser

from spinningjenny.jobs.fm_rf.cli import main_entry_point
from spinningjenny.jobs.shared.validators import valid_ecl_file


def test_entry_point(copy_testdata_tmpdir, ecl_sum):
    copy_testdata_tmpdir()
    EclSum.fwrite(ecl_sum)

    arguments = ["-s", "TEST", "-o", "rf_result"]

    main_entry_point(arguments)

    with open("rf_result") as f:
        rf_result = f.read()

    assert float(rf_result) == 0.1

    arguments = [
        "-s",
        "TEST",
        "-pk",
        "GOPT:G1",
        "-tvk",
        "ROIP:1",
        "-sd",
        "2000-01-03",
        "-ed",
        "2000-01-07",
        "-o",
        "rf_result",
    ]

    main_entry_point(arguments)

    with open("rf_result") as f:
        rf_result = f.read()

    assert float(rf_result) == 0.04

    mock_parser = MockParser()
    _ = valid_ecl_file("non_existing", mock_parser)

    assert "Could not load eclipse summary from file" in mock_parser.get_error()
