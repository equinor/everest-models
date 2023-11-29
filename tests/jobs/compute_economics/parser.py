import datetime
import pathlib
import sys
from types import SimpleNamespace
from typing import NamedTuple

from resdata.summary import Summary

from everest_models.jobs.fm_compute_economics.economic_indicator_config_model import (
    EconomicIndicatorConfig,
)


def ecl_summary_economic_indicator(*args, **kwargs):
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


def ecl_reference_summary_economic_indicator(*args, **kwargs):
    num_element = 42
    sum_keys = {
        "FOPT": [5e4 * i for i in range(num_element)],
        "FWPT": [i for i in range(num_element)],
        "FGPT": [i for i in range(num_element)],
        "FWIT": [i for i in range(num_element)],
        "FGIT": [i for i in range(num_element)],
        "GOPT:OP": [i for i in range(num_element)],
    }

    dimensions = [10, 10, 10]
    ecl_sum = Summary.writer("REFTEST", datetime.date(1999, 12, 1), *dimensions)

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


def ecl_reference_summary_economic_indicator_not_consistent(*args, **kwargs):
    num_element = 42
    sum_keys = {
        "FWPT": [i for i in range(num_element)],
        "FGPT": [i for i in range(num_element)],
        "FWIT": [i for i in range(num_element)],
        "FGIT": [i for i in range(num_element)],
        "GOPT:OP": [i for i in range(num_element)],
    }

    dimensions = [10, 10, 10]
    ecl_sum = Summary.writer("BADREFTEST", datetime.date(1999, 12, 1), *dimensions)

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


def oil_equivalent_bep(*args, **kwargs):
    return {
        "oil": {"FOPT": 1.0, "FW1PT": 0.5, "FW2PT": 0.25},
        "remap": {"FOPT": {"FOPT": 1.0}, "FWIT": {"FW1PT": 2.0, "FW2PT": 3.0}},
    }


class Options(NamedTuple):
    calculation: str
    config: EconomicIndicatorConfig
    start_date: datetime.date = None
    end_date: datetime.date = None
    ref_date: datetime.date = None
    default_exchange_rate: float = None
    default_discount_rate: float = None
    multiplier: float = 1.0
    schema: bool = None
    lint: bool = None
    output: pathlib.Path = pathlib.Path("test_0")
    output_currency: str = None


class MockParser:
    def __init__(self, options: Options):
        self._options = SimpleNamespace(
            **{k: getattr(options, k) for k in options._fields}
        )

    def parse_args(self, *args, **kwargs):
        return self._options

    def error(self, message):
        sys.stderr.write(message)
        sys.exit(2)

    def exit(self):
        sys.exit(0)
