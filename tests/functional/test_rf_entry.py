from ecl.summary import EclSum

from spinningjenny.script.fm_rf import main_entry_point
from spinningjenny import valid_ecl_file
from tests.unit.test_rf import _default_ecl_sum

from tests import tmpdir, MockParser


@tmpdir(path=None)
def test_entry_point():
    ecl_sum = _default_ecl_sum()
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
