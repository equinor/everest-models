import os
import pathlib
import shutil

import pytest
from jobs.npv.helper import _CONFIG_FILE
from jobs.npv.parser import build_argument_parser

from spinningjenny.jobs.fm_npv import cli

_INPUT_FILE = "wells.json"


@pytest.fixture
def npv_test_data_path(path_test_data):
    return path_test_data / "npv"


@pytest.fixture
def parser_mock(monkeypatch):
    monkeypatch.setattr(
        cli,
        "args_parser",
        build_argument_parser(),
    )


@pytest.fixture
def default_args():
    return [
        "--input",
        _INPUT_FILE,
        "--summary",
        "MOCKED.UNSMRY",
        "--config",
        _CONFIG_FILE,
    ]


@pytest.fixture
def copy_npv_testdata_tmpdir(npv_test_data_path, tmpdir):
    shutil.copytree(npv_test_data_path, tmpdir, dirs_exist_ok=True)
    cwd = pathlib.Path(".")
    tmpdir.chdir()
    yield
    os.chdir(cwd)


@pytest.fixture
def default_options(parser_mock, copy_npv_testdata_tmpdir, default_args):
    return cli.args_parser.parse_args(default_args)
