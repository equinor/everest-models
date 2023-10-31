import datetime

from resdata.summary import Summary


def ecl_summary(*args, **kwargs):
    sum_keys = {
        "FOPT": [2, 22, 52, 72, 82, 82],
        "FOPR": [2, 4, 6, 4, 2, 0],
        "FGPT": [2, 4, 6, 6, 8, 10],
    }
    dimensions = [10, 10, 10]
    summary = Summary.writer("TEST", datetime.date(2000, 1, 1), *dimensions)

    for key in sum_keys:
        summary.add_variable(key, wgname=None, num=0)

    for idx in range(6):
        t_step = summary.add_t_step(idx, 5 * idx)
        for key, item in sum_keys.items():
            t_step[key] = item[idx]

    return summary
