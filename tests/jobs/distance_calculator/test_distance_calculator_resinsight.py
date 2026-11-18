import math
from pathlib import Path

import numpy as np
import pytest

from everest_models.jobs.fm_distance_calculator.cli import main_entry_point
from everest_models.jobs.fm_distance_calculator.config_model import DistanceConfig
from everest_models.jobs.fm_distance_calculator.tasks import run
from everest_models.jobs.shared.resinsight import ResInsight

pytestmark = pytest.mark.resinsight

POLYGON = [[500, 500, 8335], [500, 9500, 8335]]
EARLY_DATE = "2015-06-30"
FINAL_DATE = "2024-11-09"
GRID_SHAPE_KJI = (3, 10, 10)


@pytest.fixture(scope="module")
def distance_case_path(path_test_data):
    return path_test_data / "distance_calculator" / "SPE1_CO2"


@pytest.fixture(scope="module")
def distance_case(distance_case_path):
    with ResInsight() as instance:
        case = instance.project.load_case(str(distance_case_path.with_suffix(".EGRID")))
        assert case is not None
        yield case


def _read_map(path: Path, keyword: str) -> np.ndarray:
    tokens = path.read_text(encoding="utf-8").split()
    assert tokens[0] == keyword
    assert tokens[-1] == "/"
    return np.asarray(tokens[1:-1], dtype=float)


def test_distance_calculator_cli_all_targets(
    distance_case_path, tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    config_path = distance_case_path.with_name("spe1_co2_distances.yml")

    assert (
        main_entry_point(["-c", str(config_path), "-cn", str(distance_case_path)]) == 0
    )

    # verify which cell has been selected to have minimum distance
    output = capsys.readouterr().out
    well_result = output.partition("CO2WELL  ->  well PROD\n")[2]
    assert "at ijk (7, 5, 1)" in well_result.partition("wrote scalar:")[0]

    assert float((tmp_path / "CO2FAULT").read_text()) == pytest.approx(500)
    assert float((tmp_path / "CO2WELL").read_text()) == pytest.approx(2.236067), (
        "Nearest plume cell (7, 5, 1) is 1 km west and 2 km south of PROD (8, 7, 1)"
    )
    assert float((tmp_path / "CO2POLY").read_text()) == pytest.approx(1000)

    fault_map_m = _read_map(tmp_path / "CO2FAULT_map", "CO2FAULT").reshape(
        GRID_SHAPE_KJI
    )
    cell_eastings_m = np.arange(500, 10000, 1000)
    fault_easting_m = 6000
    expected_fault_row_m = np.abs(cell_eastings_m - fault_easting_m)
    np.testing.assert_allclose(
        fault_map_m, np.broadcast_to(expected_fault_row_m, GRID_SHAPE_KJI)
    )
    well_map_km = _read_map(tmp_path / "CO2WELL_map", "CO2WELL").reshape(GRID_SHAPE_KJI)
    producer_column_km = well_map_km[:, 7 - 1, 8 - 1]
    np.testing.assert_allclose(producer_column_km, 0)
    assert well_map_km[0, 1, 1] == pytest.approx(math.hypot(6, 5))

    polygon_map_m = _read_map(tmp_path / "CO2POLY_map", "CO2POLY").reshape(
        GRID_SHAPE_KJI
    )
    assert polygon_map_m[0, 0, 0] == pytest.approx(0)
    assert polygon_map_m[0, 1, 1] == pytest.approx(1000)
    assert polygon_map_m[1, 1, 1] == pytest.approx(math.hypot(1000, 25))


@pytest.mark.parametrize(
    ("report_date", "aggregation", "expected_distance_m"),
    [
        pytest.param(EARLY_DATE, "min", 3000, id="early-plume-min"),
        pytest.param(FINAL_DATE, "min", 1000, id="final-plume-min"),
        pytest.param(None, "min", 1000, id="all-reports-min"),
        pytest.param(FINAL_DATE, "max", 7000, id="final-plume-max"),
        pytest.param(None, "mean", 4000.02332, id="all-reports-mean"),
        pytest.param(FINAL_DATE, "median", 4000, id="final-plume-median"),
    ],
)
def test_polygon_property_selection_and_aggregation(
    distance_case, tmp_path, monkeypatch, report_date, aggregation, expected_distance_m
):
    monkeypatch.chdir(tmp_path)
    calculation = {
        "type": "polygon",
        "points": POLYGON,
        "property": {"name": "sgas", "threshold": 0.01, "date": report_date},
        "output": "DISTANCE",
        "aggregation": aggregation,
    }
    config = DistanceConfig.model_validate({"distance-calculations": [calculation]})
    assert run(config, distance_case) == 0
    assert float((tmp_path / "DISTANCE").read_text()) == pytest.approx(
        expected_distance_m, abs=1e-5
    )
    assert not (tmp_path / "DISTANCE_map").exists()


@pytest.mark.parametrize(
    ("target", "property_filter", "message"),
    [
        (
            {"type": "polygon", "points": POLYGON},
            {"name": "sgas", "threshold": 0.01, "date": "2015-01-01"},
            "no finite positive distance",
        ),
        (
            {"type": "polygon", "points": POLYGON},
            {"name": "swat", "date": "2015-01-03"},
            "Report date",
        ),
        (
            {"type": "fault", "name": "MISSING"},
            None,
            "were not found",
        ),
        (
            {"type": "well", "name": "MISSING"},
            None,
            "Simulation well 'MISSING' not found",
        ),
    ],
    ids=["empty-plume", "unknown-report-date", "unknown-fault", "unknown-well"],
)
def test_calculation_without_a_result_fails(
    distance_case, tmp_path, monkeypatch, target, property_filter, message
):
    monkeypatch.chdir(tmp_path)
    calculation = {**target, "property": property_filter, "output": "DISTANCE"}
    config = DistanceConfig.model_validate({"distance-calculations": [calculation]})
    with pytest.raises(RuntimeError, match=message):
        run(config, distance_case)
    assert not (tmp_path / "DISTANCE").exists()


def test_well_distance_excludes_connected_cells(distance_case, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calculation = {
        "type": "well",
        "name": "PROD",
        "output": "DISTANCE",
    }
    config = DistanceConfig.model_validate({"distance-calculations": [calculation]})
    assert run(config, distance_case) == 0
    assert float((tmp_path / "DISTANCE").read_text()) == pytest.approx(1000), (
        "The closest cell outside PROD's completed column is one grid cell away"
    )
