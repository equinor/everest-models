import datetime

import pytest
from ecl.summary import EclSum

from spinningjenny.rf_job import recovery_factor


def _default_ecl_sum():
    sum_keys = {
        "FOPT": [i for i in range(11)],
        "FOIP": [100 for _ in range(11)],
        "GOPT:G1": [i / 2.0 for i in range(11)],
        "ROIP:1": [50 for _ in range(11)],
    }
    dimensions = [10, 10, 10]
    ecl_sum = EclSum.writer("TEST", datetime.date(2000, 1, 1), *dimensions)

    for key in sum_keys:

        sub_name = None
        if ":" in key:
            name, sub_name = key.split(":")
        else:
            name = key

        wgname = None
        num = 0
        if sub_name:
            try:
                num = int(sub_name)
            except ValueError:
                wgname = sub_name

        ecl_sum.add_variable(name, wgname=wgname, num=num)

    for val, idx in enumerate(range(0, 11, 1)):
        t_step = ecl_sum.add_t_step(idx, val)
        for key, item in sum_keys.items():
            t_step[key] = item[idx]

    return ecl_sum


@pytest.fixture
def ecl_sum():
    return _default_ecl_sum()


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
