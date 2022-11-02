import importlib
import os

from stea import SteaInput, SteaKeys, SteaResult
from sub_testdata import STEA as TEST_DATA

from spinningjenny.jobs.fm_stea.cli import main_entry_point


def test_import_stea():
    assert importlib.import_module("stea")


def calculate_patch(*args, **kwargs):
    stea_input = SteaInput(["stea_input.yml"])
    return SteaResult(
        {
            SteaKeys.KEY_VALUES: [
                {SteaKeys.TAX_MODE: SteaKeys.CORPORATE, SteaKeys.VALUES: {"NPV": 30}}
            ]
        },
        stea_input,
    )


def test_stea(copy_testdata_tmpdir, monkeypatch):
    copy_testdata_tmpdir(TEST_DATA)
    monkeypatch.setattr("stea.calculate", calculate_patch)
    # run stea job
    main_entry_point(["-c", "stea_input.yml"])
    files = os.listdir(os.getcwd())
    assert "NPV_0" in files
