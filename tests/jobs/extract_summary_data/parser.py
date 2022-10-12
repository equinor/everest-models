import datetime
from functools import partial

from ecl.summary import EclSum

from jobs.fm_extract_summary_data.parser import args_parser


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


def build_argument_parser():
    parser = args_parser
    parser._actions[1].type = ecl_summary
    return parser
