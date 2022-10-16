import datetime

import pytest

from spinningjenny.jobs.fm_rf.tasks import recovery_factor


def test_simple_usage(ecl_sum):
    assert recovery_factor(ecl_sum) == 0.1
    assert recovery_factor(ecl_sum, production_key="GOPT:G1") == 0.05
    assert recovery_factor(ecl_sum, end_date=datetime.date(2000, 1, 6)) == 0.05
    assert (
        recovery_factor(
            ecl_sum,
            start_date=datetime.date(2000, 1, 3),
            end_date=datetime.date(2000, 1, 7),
        )
        == 0.04
    )
    assert (
        recovery_factor(
            ecl_sum,
            production_key="GOPT:G1",
            start_date=datetime.date(2000, 1, 3),
            end_date=datetime.date(2000, 1, 7),
        )
        == 0.02
    )
    assert (
        recovery_factor(
            ecl_sum,
            production_key="GOPT:G1",
            total_volume_key="ROIP:1",
            start_date=datetime.date(2000, 1, 3),
            end_date=datetime.date(2000, 1, 7),
        )
        == 0.04
    )


def test_clamping_behaviour(ecl_sum):
    # outside of date range, clamping to start and end
    assert (
        recovery_factor(
            ecl_sum,
            start_date=datetime.date(1999, 1, 1),
            end_date=datetime.date(2000, 1, 6),
        )
        == 0.05
    )
    assert recovery_factor(ecl_sum, end_date=datetime.date(2001, 1, 1)) == 0.1


def test_exceptions(ecl_sum):

    with pytest.raises(ValueError) as excinfo:
        recovery_factor(
            ecl_sum,
            start_date=datetime.date(2001, 1, 5),
            end_date=datetime.date(2000, 1, 3),
        )

    assert "Invalid time interval start after end" in str(excinfo.value)

    with pytest.raises(KeyError) as excinfo:
        recovery_factor(ecl_sum, production_key="NON-EXISTING")

    assert "Summary case does not have key:NON-EXISTING" in str(excinfo.value)

    with pytest.raises(KeyError) as excinfo:
        recovery_factor(ecl_sum, total_volume_key="NON-EXISTING")

    assert "No such key:NON-EXISTING" in str(excinfo.value)
