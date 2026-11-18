import math
from pathlib import Path

import numpy as np
import pytest

from everest_models.jobs.fm_distance_calculator.cli import main_entry_point
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
    ("selection", "expected_distance_m"),
    [
        ({"output-date": EARLY_DATE}, 3000),
        ({"output-date": FINAL_DATE}, 1000),
        ({}, 1000),
        ({"output-date": FINAL_DATE, "aggregation": "max"}, 7000),
        ({"aggregation": "mean"}, 4000.02332),
        ({"output-date": FINAL_DATE, "aggregation": "median"}, 4000),
        (
            {
                "property": ["sgas", "swat"],
                "property-threshold": [0.01, 0.97],
                "output-date": [EARLY_DATE, FINAL_DATE],
            },
            math.hypot(4000, 65),
        ),
    ],
    ids=[
        "early-plume-min",
        "final-plume-min",
        "all-reports-min",
        "final-plume-max",
        "all-reports-mean",
        "final-plume-median",
        "early-gas-and-final-water",
    ],
)
def test_polygon_property_selection_and_aggregation(
    distance_case, tmp_path, monkeypatch, selection, expected_distance_m
):
    monkeypatch.chdir(tmp_path)
    calculation = {
        "type": "polygon-distance",
        "polygon-input": POLYGON,
        "property": "sgas",
        "property-threshold": 0.01,
        "output-name": "DISTANCE",
        **selection,
    }
    assert run({"distance-calculations": [calculation]}, distance_case) == 0
    assert float((tmp_path / "DISTANCE").read_text()) == pytest.approx(
        expected_distance_m, abs=1e-5
    )
    assert not (tmp_path / "DISTANCE_map").exists()


@pytest.mark.parametrize(
    ("selection", "message"),
    [
        ({"output-date": "2015-01-01"}, "no finite positive distance"),
        ({"property": "swat", "output-date": "2015-01-03"}, "Report date"),
        (
            {"type": "fault-distance", "fault-name": "MISSING"},
            "were not found",
        ),
        (
            {"type": "well-distance", "well-name": "MISSING"},
            "Simulation well 'MISSING' not found",
        ),
    ],
    ids=["empty-plume", "unknown-report-date", "unknown-fault", "unknown-well"],
)
def test_calculation_without_a_result_fails(
    distance_case, tmp_path, monkeypatch, selection, message
):
    monkeypatch.chdir(tmp_path)
    calculation = {
        "type": "polygon-distance",
        "polygon-input": POLYGON,
        "property": "sgas",
        "property-threshold": 0.01,
        "output-name": "DISTANCE",
        **selection,
    }
    with pytest.raises(RuntimeError, match=message):
        run({"distance-calculations": [calculation]}, distance_case)
    assert not (tmp_path / "DISTANCE").exists()


def test_well_distance_excludes_connected_cells(distance_case, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calculation = {
        "type": "well-distance",
        "well-name": "PROD",
        "output-name": "DISTANCE",
    }
    assert run({"distance-calculations": [calculation]}, distance_case) == 0
    assert float((tmp_path / "DISTANCE").read_text()) == pytest.approx(1000), (
        "The closest cell outside PROD's completed column is one grid cell away"
    )
