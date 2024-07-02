from pathlib import Path

import pytest
from everest_models.jobs.fm_well_trajectory.models.config import ConfigSchema
from everest_models.jobs.shared.io_utils import load_yaml
from pydantic import ValidationError
from sub_testdata import WELL_TRAJECTORY as TEST_DATA


def test_parameters_config_simple(path_test_data):
    config = load_yaml(path_test_data / TEST_DATA / "simple" / "config.yml")
    ConfigSchema.model_validate(config)


def test_parameters_config_resinsight(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "spe1case1")
    config = load_yaml("config.yml")
    ConfigSchema.model_validate(config)


def test_parameters_invalid_platform(path_test_data):
    config = load_yaml(path_test_data / TEST_DATA / "simple" / "config.yml")
    config["wells"][0]["platform"] = "platform0"
    with pytest.raises(
        ValidationError, match="Platform 'platform0' for well 'WI_1' not defined"
    ):
        ConfigSchema.model_validate(config)
