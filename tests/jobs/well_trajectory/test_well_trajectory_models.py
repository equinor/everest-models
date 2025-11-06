from pathlib import Path

import pytest
from pydantic import ValidationError
from sub_testdata import WELL_TRAJECTORY as TEST_DATA

from everest_models.jobs.fm_well_trajectory.models.config import (
    ConfigSchema,
    InterpolationConfig,
)
from everest_models.jobs.fm_well_trajectory.read_trajectories import read_trajectories
from everest_models.jobs.shared.io_utils import load_yaml


def test_interpolation_config():
    with pytest.raises(
        ValidationError,
        match=r"Interpolation type 'simple': 'measured_depth_step' not allowed",
    ):
        InterpolationConfig.model_validate({"type": "simple", "measured_depth_step": 1})
    with pytest.raises(
        ValidationError,
        match=r"Interpolation type 'resinsight': fields not allowed: \['length', 'trial_number', 'trial_step'\]",
    ):
        InterpolationConfig.model_validate(
            {"type": "resinsight", "length": 1, "trial_step": 0.1}
        )


def test_parameters_config_simple(path_test_data):
    config = load_yaml(path_test_data / TEST_DATA / "simple" / "config.yml")
    ConfigSchema.model_validate(config)


def test_parameters_config_resinsight(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    config = load_yaml("config.yml")
    ConfigSchema.model_validate(config)


def test_parameters_invalid_platform(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    config = load_yaml("config.yml")
    config["wells"][0]["platform"] = "platform0"

    with pytest.raises(
        SystemExit, match="Some wells refer to undefined platforms:.*platform0"
    ):
        config = ConfigSchema.model_validate(config)
        read_trajectories(config.wells, config.platforms)
