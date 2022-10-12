import datetime

from ecl.summary import EclSum


def ecl_summary_npv(*args, **kwargs):
    num_element = 42
    sum_keys = {
        "FOPT": [10e4 * i for i in range(num_element)],
        "FWPT": [i for i in range(num_element)],
        "FGPT": [i for i in range(num_element)],
        "FWIT": [i for i in range(num_element)],
        "FGIT": [i for i in range(num_element)],
        "GOPT:OP": [i for i in range(num_element)],
    }

    dimensions = [10, 10, 10]
    ecl_sum = EclSum.writer("TEST", datetime.date(1999, 12, 1), *dimensions)

    for key in sum_keys:
        sub_name = None
        if ":" in key:
            name, sub_name = key.split(":")
        else:
            name = key

        if sub_name:
            ecl_sum.add_variable(name, wgname=sub_name)
        else:
            ecl_sum.add_variable(name)

    for val, idx in enumerate(range(num_element)):
        t_step = ecl_sum.add_t_step(idx, 30 * val)
        for key, item in sum_keys.items():
            t_step[key] = item[idx]

    return ecl_sum


def ecl_summary(*args, **kwargs):
    sum_keys = {
        "FOPT": [2, 22, 52, 72, 82, 82],
        "FOPR": [2, 4, 6, 4, 2, 0],
        "FGPT": [2, 4, 6, 6, 8, 10],
    }
    dimensions = [10, 10, 10]
    ecl_sum = EclSum.writer("TEST", datetime.date(2000, 1, 1), *dimensions)

    for key in sum_keys:
        ecl_sum.add_variable(key, wgname=None, num=0)

    for idx in range(6):
        t_step = ecl_sum.add_t_step(idx, 5 * idx)
        for key, item in sum_keys.items():
            t_step[key] = item[idx]

    return ecl_sum
