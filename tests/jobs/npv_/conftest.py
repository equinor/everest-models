import datetime
import os
import shutil

import pytest
from ecl.summary import EclSum
from jobs.npv_.helper import _CONFIG_FILE

from jobs.fm_npv import cli

_INPUT_FILE = "wells.json"


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


@pytest.fixture
def npv_test_data_path(path_test_data):
    return str(path_test_data / "npv") + "/"


@pytest.fixture
def options(monkeypatch, tmpdir, npv_test_data_path):
    for file_name in os.listdir(npv_test_data_path):
        shutil.copy(npv_test_data_path + file_name, tmpdir.strpath)
    monkeypatch.setattr(
        cli,
        "valid_ecl_file",
        ecl_summary_npv,
    )
    cwd = os.getcwd()
    tmpdir.chdir()

    parser = cli._build_parser()
    args = [
        "--input",
        _INPUT_FILE,
        "--summary",
        "MOCKED.UNSMRY",
        "--config",
        _CONFIG_FILE,
    ]

    yield parser.parse_args(args)

    os.chdir(cwd)
