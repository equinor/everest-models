from utils import relpath, tmpdir

from jobs.utils.io_utils import load_yaml

TEST_DATA_PATH = relpath("tests", "testdata", "misc")


@tmpdir(TEST_DATA_PATH)
def test_load_yaml_supports_scientific_notation():
    res = load_yaml("input.json")
    assert res["test"]["1"] == 1e-06
    assert res["test"]["2"] == 1e-05
    assert res["test"]["3"] == 0.01
