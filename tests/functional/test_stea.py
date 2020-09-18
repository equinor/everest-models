from tests import tmpdir, relpath
from spinningjenny.script.fm_stea import main_entry_point
import importlib
from mock import patch
from stea import SteaResult, SteaKeys, SteaInput
import os

TEST_DATA_PATH = relpath("tests", "testdata", "stea")


def test_import_stea():
    assert importlib.import_module("stea")


@tmpdir(TEST_DATA_PATH)
def calculate_patch():
    stea_input = SteaInput(["stea_input.yml"])
    return SteaResult(
        {
            SteaKeys.KEY_VALUES: [
                {SteaKeys.TAX_MODE: SteaKeys.CORPORATE, SteaKeys.VALUES: {"NPV": 30}}
            ]
        },
        stea_input,
    )


@patch("stea.calculate", return_value=calculate_patch())
@tmpdir(TEST_DATA_PATH)
def test_stea(stea_calculate_mock):
    # run stea job
    main_entry_point(["-c", "stea_input.yml"])
    stea_calculate_mock.assert_called_once()
    files = os.listdir(os.getcwd())
    assert "NPV_0" in files
