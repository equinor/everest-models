import datetime
import pathlib
import sys
from typing import NamedTuple

from everest_models.jobs.fm_npv.npv_config_model import NPVConfig
from everest_models.jobs.shared.models import WellConfig
from resdata.summary import Summary


def ecl_summary_npv(*args, **kwargs):
    num_element = 42
    sum_keys = {
        "FOPT": [10e4 * i for i in range(num_element)],
        "FWPT": list(range(num_element)),
        "FGPT": list(range(num_element)),
        "FWIT": list(range(num_element)),
        "FGIT": list(range(num_element)),
        "GOPT:OP": list(range(num_element)),
    }

    dimensions = [10, 10, 10]
    ecl_sum = Summary.writer("TEST", datetime.date(1999, 12, 1), *dimensions)

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


class Options(NamedTuple):
    config: NPVConfig
    input: WellConfig = None
    start_date: datetime.date = None
    end_date: datetime.date = None
    ref_date: datetime.date = None
    default_exchange_rate: float = None
    default_discount_rate: float = None
    schema: bool = None
    lint: bool = None
    multiplier: float = 1.0
    summary: Summary = ecl_summary_npv()
    output: pathlib.Path = pathlib.Path("test_0")


class MockParser:
    def __init__(self, options: Options):
        self._options = options

    def parse_args(self, *args, **kwargs):
        return self._options

    def error(self, message):
        sys.stderr.write(message)
        sys.exit(2)

    def exit(self):
        sys.exit(0)
