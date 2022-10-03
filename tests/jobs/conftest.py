import os
import pathlib
import shutil

import pytest


@pytest.fixture
def path_test_data() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent / "testdata"


@pytest.fixture
def sub_testdata(request, path_test_data) -> pathlib.Path:
    if (marker := request.node.get_closest_marker("sub_dir")) is None:
        raise ValueError("please add 'sub_dir' marker")
    return path_test_data / marker.args[0]


@pytest.fixture
def copy_testdata_tmpdir(sub_testdata, tmpdir):
    shutil.copytree(sub_testdata, tmpdir.strpath, dirs_exist_ok=True)
    cwd = pathlib.Path(".")
    tmpdir.chdir()
    yield tmpdir
    os.chdir(cwd)
