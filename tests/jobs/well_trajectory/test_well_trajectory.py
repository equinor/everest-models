import copy
from pathlib import Path

import numpy as np
import pytest
from everest_models.jobs.fm_well_trajectory.models.config import ConfigSchema
from everest_models.jobs.fm_well_trajectory.read_trajectories import read_trajectories
from everest_models.jobs.shared.io_utils import load_yaml
from sub_testdata import WELL_TRAJECTORY as TEST_DATA


@pytest.fixture(scope="module")
def well_trajectory_config(path_test_data):
    return load_yaml(path_test_data / TEST_DATA / "config.yml")


def test_read_trajectories(well_trajectory_config, copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    config = ConfigSchema.model_validate(well_trajectory_config)

    trajectories1 = read_trajectories(
        config.scales, config.references, config.wells, config.platforms
    )

    for key in trajectories1:
        for field in ["x", "y", "z"]:
            assert len(getattr(trajectories1[key], field)) == 5
        assert trajectories1[key].z[1] == 200


def test_read_trajectories_platform_fallback(
    well_trajectory_config, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)
    config = ConfigSchema.model_validate(well_trajectory_config)

    Path("platform_k.json").unlink()

    trajectories1 = read_trajectories(
        config.scales, config.references, config.wells, config.platforms
    )
    for key in trajectories1:
        for field in ["x", "y", "z"]:
            assert len(getattr(trajectories1[key], field)) == 5
        assert trajectories1[key].z[1] == 200


def test_read_trajectories_no_platform(well_trajectory_config, copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    config = ConfigSchema.model_validate(well_trajectory_config)

    trajectories1 = read_trajectories(
        config.scales, config.references, config.wells, config.platforms
    )

    Path("platform_k.json").unlink()

    trajectories2 = read_trajectories(
        config.scales, config.references, config.wells, []
    )
    for key in trajectories1:
        for field in ["x", "y", "z"]:
            assert np.all(
                np.equal(
                    getattr(trajectories1[key], field)[2:],
                    getattr(trajectories2[key], field),
                )
            )


def test_read_trajectories_no_kickof(well_trajectory_config, copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    config = ConfigSchema.model_validate(well_trajectory_config)

    trajectories1 = read_trajectories(
        config.scales, config.references, config.wells, config.platforms
    )

    for key in trajectories1:
        for field in ["x", "y", "z"]:
            assert len(getattr(trajectories1[key], field)) == 5

    Path("platform_k.json").unlink()

    new_config = copy.deepcopy(well_trajectory_config)
    del new_config["platforms"][0]["k"]
    del new_config["platforms"][1]["k"]
    config = ConfigSchema.model_validate(new_config)
    trajectories2 = read_trajectories(
        config.scales, config.references, config.wells, config.platforms
    )
    for key in trajectories1:
        for field in ["x", "y", "z"]:
            assert np.all(
                np.equal(
                    np.delete(getattr(trajectories1[key], field), 1),
                    getattr(trajectories2[key], field),
                )
            )
