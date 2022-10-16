import datetime

from ecl.summary import EclSum

from spinningjenny.jobs.fm_npv.parser import args_parser


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


def build_argument_parser():
    parser = args_parser
    parser._actions[1].type = ecl_summary_npv
    return parser
