import builtins
import json
import logging
import os
import sys
from importlib.util import find_spec
from pathlib import Path

import pytest
from sub_testdata import WELL_TRAJECTORY as TEST_DATA

if find_spec("rips") is None:
    pytest.skip("Skipping tests: 'rips' is not installed", allow_module_level=True)

from everest_models.jobs.fm_well_trajectory.cli import main_entry_point
from everest_models.jobs.fm_well_trajectory.well_trajectory_resinsight import ResInsight

_builtin_import = builtins.__import__


@pytest.fixture(scope="module")
def well_trajectory_arguments():
    return ["-c", "config.yml", "-E", "SPE1CASE1"]


def _nonempty_file(p: Path) -> bool:
    return p.is_file() and p.stat().st_size > 0


def _assert_schedule_files_present_with_keywords(
    cwd: Path, expected_schedule_files: set[str]
) -> None:
    wells = {p.stem for p in cwd.glob("*.SCH") if _nonempty_file(p)}
    for well in expected_schedule_files:
        assert well in wells, (
            f"Expected schedule file {well}.SCH not found in created SCH files."
        )
        sch = cwd / f"{well}.SCH"
        text = sch.read_text(encoding="utf-8", errors="ignore")
        if well.endswith("_MSW"):
            # Multisegmenten schedule file
            assert "WELSEGS" in text, f"{sch} missing WELSEGS section"
            assert "COMPSEGS" in text, f"{sch} missing COMPSEGS section"
        else:
            # Regular schedule file
            assert "WELSPECS" in text, f"{sch} missing WELSPECS section"
            assert "COMPDAT" in text, f"{sch} missing COMPDAT section"


def _assert_deviation_files_nonempty(
    wellpaths_dir: Path, expected_deviation_files: set[str]
) -> None:
    assert wellpaths_dir.is_dir(), "wellpaths/ directory was not created."
    for well in expected_deviation_files:
        wp = wellpaths_dir / f"{well}.dev"
        assert _nonempty_file(wp), (
            f"Well trajectory file for {well}.dev is missing or empty."
        )


@pytest.mark.slow
@pytest.mark.resinsight
def test_failing_start_resinsight(caplog):
    caplog.set_level(logging.INFO)
    with (
        pytest.raises(
            ConnectionError,
            match="Failed to launch ResInsight executable: _non_existing_binary_",
        ),
        ResInsight("_non_existing_binary_"),
    ):
        pass
    assert "Launching ResInsight..." in caplog.text


@pytest.mark.resinsight
@pytest.mark.parametrize(
    ["module", "msg"],
    [
        ("rips", "Failed to launch ResInsight: module `rips` not found"),
        ("lasio", "Failed to read LAS file: module `lasio` not found"),
    ],
)
def test_rips_not_installed(
    well_trajectory_arguments, copy_testdata_tmpdir, monkeypatch, module, msg
):
    def _import(name, *args, **kwargs):
        if name == module:
            raise ModuleNotFoundError()
        return _builtin_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _import)
    for mod in (
        module,
        "everest_models.jobs.fm_well_trajectory.cli",
        "everest_models.jobs.fm_well_trajectory.well_trajectory_resinsight",
        "everest_models.jobs.fm_well_trajectory.resinsight",
    ):
        monkeypatch.delitem(sys.modules, mod, raising=False)
    from everest_models.jobs.fm_well_trajectory.cli import (  # noqa: PLC0415
        main_entry_point,
    )

    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    for path in Path.cwd().glob("mlt_*.json"):
        path.unlink()

    with pytest.raises(ImportError, match=msg):
        main_entry_point(well_trajectory_arguments)


@pytest.mark.resinsight
def test_start_resinsight(caplog):
    with ResInsight() as ri:
        assert ri.project.cases() == []
    assert "Launching ResInsight..." in caplog.text


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_lint(
    well_trajectory_arguments, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    with pytest.raises(SystemExit):
        main_entry_point([*well_trajectory_arguments, "--lint"])

    assert not any(
        path.relative_to("expected").exists() for path in Path("expected").glob("**/*")
    )


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_no_mlt(
    well_trajectory_arguments, copy_testdata_tmpdir
):
    expected_dev_files = ["INJ", "PROD"]
    expected_sch_files = ["INJ", "PROD", "INJ_MSW", "PROD_MSW"]

    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    for path in Path.cwd().glob("mlt_*.json"):
        path.unlink()
    main_entry_point(well_trajectory_arguments)

    _assert_schedule_files_present_with_keywords(Path.cwd(), expected_sch_files)
    _assert_deviation_files_nonempty(Path.cwd() / "wellpaths", expected_dev_files)


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_mlt(
    well_trajectory_arguments, copy_testdata_tmpdir
):
    expected_dev_files = [
        "INJ",
        "PROD",
        "INJ_Y1",
        "INJ_Y2",
        "INJ_Y3",
        "PROD_Y1",
        "PROD_Y2",
    ]
    expected_sch_files = [
        "INJ_Y1",
        "INJ_Y2",
        "INJ_Y3",
        "INJ_Y1_MSW",
        "INJ_Y2_MSW",
        "INJ_Y3_MSW",
        "PROD_Y1",
        "PROD_Y2",
        "PROD_Y1_MSW",
        "PROD_Y2_MSW",
    ]

    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    main_entry_point(well_trajectory_arguments)

    _assert_schedule_files_present_with_keywords(Path.cwd(), expected_sch_files)
    _assert_deviation_files_nonempty(Path.cwd() / "wellpaths", expected_dev_files)


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_mixed(
    well_trajectory_arguments, copy_testdata_tmpdir
):
    expected_dev_files = ["INJ", "PROD", "INJ_Y1", "INJ_Y2", "INJ_Y3", "PROD"]
    expected_sch_files = [
        "INJ_Y1",
        "INJ_Y2",
        "INJ_Y3",
        "INJ_Y1_MSW",
        "INJ_Y2_MSW",
        "INJ_Y3_MSW",
        "PROD",
        "PROD_MSW",
    ]

    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    for path in Path.cwd().glob("mlt_*.json"):
        with path.open(encoding="utf-8") as fp:
            guide_points = json.load(fp)
        del guide_points["PROD"]
        with path.open("w", encoding="utf-8") as fp:
            json.dump(guide_points, fp)
    main_entry_point(well_trajectory_arguments)

    _assert_schedule_files_present_with_keywords(Path.cwd(), expected_sch_files)
    _assert_deviation_files_nonempty(Path.cwd() / "wellpaths", expected_dev_files)


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_no_mlt_static_perforation(
    copy_testdata_tmpdir,
):
    expected_dev_files = ["INJ", "PROD"]
    expected_sch_files = ["INJ", "PROD", "INJ_MSW", "PROD_MSW"]

    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    for path in Path.cwd().glob("mlt_*.json"):
        path.unlink()
    main_entry_point(["-c", "config_static_perforation.yml", "-E", "SPE1CASE1"])

    _assert_schedule_files_present_with_keywords(Path.cwd(), expected_sch_files)
    _assert_deviation_files_nonempty(Path.cwd() / "wellpaths", expected_dev_files)


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_no_mlt_dynamic_perforation(
    copy_testdata_tmpdir,
):
    expected_dev_files = ["INJ", "PROD"]
    expected_sch_files = ["INJ", "PROD", "INJ_MSW", "PROD_MSW"]

    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    for path in Path.cwd().glob("mlt_*.json"):
        path.unlink()
    main_entry_point(["-c", "config_dynamic_perforation.yml", "-E", "SPE1CASE1"])

    _assert_schedule_files_present_with_keywords(Path.cwd(), expected_sch_files)
    _assert_deviation_files_nonempty(Path.cwd() / "wellpaths", expected_dev_files)


@pytest.mark.resinsight
def test_well_trajectory_resinsight_main_entry_point_no_mlt_missing_date(
    copy_testdata_tmpdir,
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    for path in Path.cwd().glob("mlt_*.json"):
        path.unlink()
    with pytest.raises(
        RuntimeError,
        match="Connections error: date not found in restart file: 2015-01-03",
    ):
        main_entry_point(["-c", "config_missing_date.yml", "-E", "SPE1CASE1"])


@pytest.mark.parametrize("remove_file", ["SPE1CASE1.EGRID", "SPE1CASE1.INIT"])
def test_checking_for_files_required_for_model(
    remove_file, copy_testdata_tmpdir, capsys
):
    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    os.remove(remove_file)
    with pytest.raises(SystemExit) as excinfo:
        main_entry_point(["-c", "config.yml", "-E", "SPE1CASE1"])
    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert f"Missing {remove_file} file" in captured.err


def test_validate_files_required_for_dynamic_perforation(copy_testdata_tmpdir, capsys):
    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    os.remove("SPE1CASE1.UNRST")
    with pytest.raises(SystemExit) as excinfo:
        main_entry_point(["-c", "config_dynamic_perforation.yml", "-E", "SPE1CASE1"])
    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert "Missing SPE1CASE1.UNRST file" in captured.err


def test_specifying_eclipse_model_with_extension(copy_testdata_tmpdir):
    copy_testdata_tmpdir(Path(TEST_DATA) / "resinsight")
    main_entry_point(["-c", "config.yml", "-E", "SPE1CASE1.EGRID"])
