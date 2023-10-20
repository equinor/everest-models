import copy

import pytest
from pydantic import ValidationError
from sub_testdata import WELL_TRAJECTORY as TEST_DATA

from everest_models.jobs.fm_well_trajectory.models.config import ConfigSchema
from everest_models.jobs.shared.validators import _valid_yaml


@pytest.fixture(scope="module")
def well_trajectory_config(path_test_data):
    return _valid_yaml(path_test_data / TEST_DATA / "config.yml")


def test_parameters_config(well_trajectory_config):
    ConfigSchema.parse_obj(well_trajectory_config)


def test_parameters_invalid_platform(well_trajectory_config):
    config = copy.deepcopy(well_trajectory_config)
    config["wells"][0]["platform"] = "platform0"
    with pytest.raises(
        ValidationError, match="Platform 'platform0' for well 'WI_1' not defined"
    ):
        ConfigSchema.parse_obj(config)
