from sub_testdata import MISC as TEST_DATA

from spinningjenny.jobs.utils.io_utils import load_yaml


def test_load_yaml_supports_scientific_notation(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    res = load_yaml("input.json")
    assert res["test"]["1"] == 1e-06
    assert res["test"]["2"] == 1e-05
    assert res["test"]["3"] == 0.01
