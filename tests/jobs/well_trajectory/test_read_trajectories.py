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
    return load_yaml(path_test_data / Path(TEST_DATA) / "simple" / "config.yml")


def test_read_trajectories(well_trajectory_config, copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
    config = ConfigSchema.model_validate(well_trajectory_config)

    trajectories1 = read_trajectories(
        config.scales, config.references, config.wells, config.platforms
    )

    for key in trajectories1:
        for field in ["x", "y", "z"]:
            assert len(getattr(trajectories1[key], field)) == 5
        assert trajectories1[key].z[1] == 200


def test_read_trajectories_missing_file(well_trajectory_config, copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
    Path("p2_b.json").unlink()
    Path("p3_y.json").unlink()
    config = ConfigSchema.model_validate(well_trajectory_config)

    with pytest.raises(ValueError, match=r"Missing point files: \['p2_b', 'p3_y'\]"):
        read_trajectories(
            config.scales, config.references, config.wells, config.platforms
        )


def test_read_trajectories_platform_fallback(
    well_trajectory_config, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
    config = ConfigSchema.model_validate(well_trajectory_config)

    Path("platform_k.json").unlink()

    trajectories1 = read_trajectories(
        config.scales, config.references, config.wells, config.platforms
    )
    for key in trajectories1:
        for field in ["x", "y", "z"]:
            assert len(getattr(trajectories1[key], field)) == 5
        # platform and kickoff position:
        assert trajectories1[key].z[0] == 0
        assert trajectories1[key].z[1] == 200
        # platform and kickoff are in the same lateral position:
        assert trajectories1[key].x[0] == trajectories1[key].x[1]
        assert trajectories1[key].y[0] == trajectories1[key].y[1]


def test_read_trajectories_no_platform(well_trajectory_config, copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
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
                    getattr(trajectories2[key], field)[1:],
                )
            )
        # platform added at the same location as the first guide point:
        assert trajectories2[key].x[0] == trajectories2[key].x[1]
        assert trajectories2[key].y[0] == trajectories2[key].y[1]


def test_read_trajectories_no_kickoff(well_trajectory_config, copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
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
