import datetime

import pytest
from ecl.summary import EclSum


@pytest.fixture
def ecl_sum():
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
