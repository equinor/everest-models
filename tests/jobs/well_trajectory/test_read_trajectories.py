from pathlib import Path

import numpy as np
import pytest
from sub_testdata import WELL_TRAJECTORY as TEST_DATA

from everest_models.jobs.fm_well_trajectory.models.config import ConfigSchema
from everest_models.jobs.fm_well_trajectory.read_trajectories import (
    read_laterals,
    read_trajectories,
)
from everest_models.jobs.shared.io_utils import dump_json, load_json, load_yaml


def test_read_trajectories(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
    config = ConfigSchema.model_validate(load_yaml("config.yml"))

    trajectories1 = read_trajectories(config.wells, config.platforms)

    for key in trajectories1:
        for field in ["x", "y", "z"]:
            assert len(getattr(trajectories1[key], field)) == 5
        assert trajectories1[key].z[1] == 200


def test_read_trajectories_missing_file(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
    Path("p2_b.json").unlink()
    Path("p3_y.json").unlink()
    config = ConfigSchema.model_validate(load_yaml("config.yml"))

    with pytest.raises(ValueError, match=r"Missing point files: \['p2_b', 'p3_y'\]"):
        read_trajectories(config.wells, config.platforms)


def test_read_trajectories_missing_well(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
    p2_b = load_json("p2_b.json")
    del p2_b["OP_4"]
    dump_json(p2_b, Path("p2_b.json"))
    config = ConfigSchema.model_validate(load_yaml("config.yml"))

    with pytest.raises(ValueError, match=r"Missing wells: \['p2_b/OP_4'\]"):
        read_trajectories(config.wells, config.platforms)


def test_read_trajectories_platform_fallback(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
    config = ConfigSchema.model_validate(load_yaml("config.yml"))

    Path("platform_k.json").unlink()

    trajectories1 = read_trajectories(config.wells, config.platforms)
    for key in trajectories1:
        for field in ["x", "y", "z"]:
            assert len(getattr(trajectories1[key], field)) == 5
        # platform and kickoff position:
        assert trajectories1[key].z[0] == 0
        assert trajectories1[key].z[1] == 200
        # platform and kickoff are in the same lateral position:
        assert trajectories1[key].x[0] == trajectories1[key].x[1]
        assert trajectories1[key].y[0] == trajectories1[key].y[1]


def test_read_trajectories_no_platform(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
    config = ConfigSchema.model_validate(load_yaml("config.yml"))

    trajectories1 = read_trajectories(config.wells, config.platforms)

    Path("platform_k.json").unlink()

    trajectories2 = read_trajectories(config.wells, [])
    for key in trajectories1:
        for field in ["x", "y", "z"]:
            # No platform means no kickoff, so the kickoff point is not there:
            assert np.all(
                np.equal(
                    getattr(trajectories1[key], field)[2:],
                    getattr(trajectories2[key], field)[1:],
                )
            )
        # platform added at the same location as the first guide point:
        assert trajectories2[key].x[0] == trajectories2[key].x[1]
        assert trajectories2[key].y[0] == trajectories2[key].y[1]


def test_read_trajectories_no_kickoff(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "simple")
    config = ConfigSchema.model_validate(load_yaml("config.yml"))

    trajectories1 = read_trajectories(config.wells, config.platforms)

    for key in trajectories1:
        for field in ["x", "y", "z"]:
            assert len(getattr(trajectories1[key], field)) == 5

    Path("platform_k.json").unlink()

    new_config = load_yaml("config.yml")
    del new_config["platforms"][0]["k"]
    del new_config["platforms"][1]["k"]
    config = ConfigSchema.model_validate(new_config)
    trajectories2 = read_trajectories(config.wells, config.platforms)
    for key in trajectories1:
        for field in ["x", "y", "z"]:
            # Everything is the same, except the kickoff point is missing:
            assert np.all(
                np.equal(
                    np.delete(getattr(trajectories1[key], field), 1),
                    getattr(trajectories2[key], field),
                )
            )


def test_read_laterals_orphaned_branches(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "read_laterals")
    config = ConfigSchema.model_validate(load_yaml("config.yml"))
    mlt_p1_z = load_json("mlt_p1_z.json")
    mlt_p1_z["DUMMY"] = {"1": 0.0}
    dump_json(mlt_p1_z, Path("mlt_p1_z.json"))
    with pytest.raises(
        ValueError, match=r"Found branches without parent well: \['DUMMY'\]"
    ):
        read_laterals(config.wells)


def test_read_laterals_missing_files(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "read_laterals")
    config = ConfigSchema.model_validate(load_yaml("config.yml"))
    Path("mlt_p2_b.json").unlink()
    Path("mlt_p3_x.json").unlink()
    with pytest.raises(
        ValueError,
        match=r"Missing coordinate files: '\['mlt_p2_b', 'mlt_p3_x'\]'",
    ):
        read_laterals(config.wells)


def test_read_laterals_missing_wells(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "read_laterals")
    config = ConfigSchema.model_validate(load_yaml("config.yml"))
    mlt_p2_b = load_json("mlt_p2_b.json")
    mlt_p3_x = load_json("mlt_p3_x.json")
    del mlt_p2_b["INJ"]
    del mlt_p3_x["PROD"]
    dump_json(mlt_p2_b, Path("mlt_p2_b.json"))
    dump_json(mlt_p3_x, Path("mlt_p3_x.json"))
    with pytest.raises(
        ValueError,
        match=r"Missing wells in coordinate files: \['mlt_p2_b/INJ', 'mlt_p3_x/PROD'\]",
    ):
        read_laterals(config.wells)


def test_read_laterals_missing_branches(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "read_laterals")
    config = ConfigSchema.model_validate(load_yaml("config.yml"))
    mlt_p2_b = load_json("mlt_p2_b.json")
    mlt_p3_x = load_json("mlt_p3_x.json")
    del mlt_p2_b["INJ"]["1"]
    del mlt_p3_x["PROD"]["2"]
    dump_json(mlt_p2_b, Path("mlt_p2_b.json"))
    dump_json(mlt_p3_x, Path("mlt_p3_x.json"))
    with pytest.raises(
        ValueError,
        match=r"Missing branches in coordinate files: \['mlt_p2_b/INJ/1', 'mlt_p3_x/PROD/2'\]",
    ):
        read_laterals(config.wells)


def test_read_laterals_branch_not_on_well(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "read_laterals")
    config = ConfigSchema.model_validate(load_yaml("config.yml"))
    mlt_p1_z = load_json("mlt_p1_z.json")
    mlt_p1_z["INJ"]["1"] = 8475
    dump_json(mlt_p1_z, Path("mlt_p1_z.json"))
    with pytest.raises(ValueError, match=r"Branch '1' does not start on well 'INJ'"):
        read_laterals(config.wells)


def test_read_laterals(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "read_laterals")
    config = ConfigSchema.model_validate(load_yaml("config.yml"))
    laterals = read_laterals(config.wells)

    assert laterals["INJ"]["1"][0] == pytest.approx(8350)
    assert laterals["INJ"]["2"][0] == pytest.approx(8375)
    assert laterals["PROD"]["2"][0] == pytest.approx(8325)

    assert np.allclose(laterals["INJ"]["1"][1].x, [2500, 1500, 500], rtol=1e-4)
    assert np.allclose(laterals["INJ"]["1"][1].y, 2500, rtol=1e-4)
    assert np.allclose(laterals["INJ"]["1"][1].z, 8350, rtol=1e-4)

    assert np.allclose(laterals["INJ"]["2"][1].x, 2500, rtol=1e-4)
    assert np.allclose(laterals["INJ"]["2"][1].y, [2500, 6000, 9500], rtol=1e-4)
    assert np.allclose(laterals["INJ"]["2"][1].z, 8375, rtol=1e-4)

    assert np.allclose(laterals["PROD"]["2"][1].x, [7500, 8750, 10000], rtol=1e-4)
    assert np.allclose(laterals["PROD"]["2"][1].y, [7500, 8750, 10000], rtol=1e-4)
    assert np.allclose(laterals["PROD"]["2"][1].z, [8325, 8375, 8425], rtol=1e-4)
