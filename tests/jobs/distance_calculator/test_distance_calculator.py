import math
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from everest_models.forward_models import get_forward_models
from everest_models.jobs.fm_distance_calculator import tasks as distance_tasks
from everest_models.jobs.fm_distance_calculator.cli import load_config
from everest_models.jobs.fm_distance_calculator.parser import build_argument_parser
from everest_models.jobs.fm_distance_calculator.tasks import (
    _resolve_unit_conversion,
    aggregate_distance,
    parse_polygon_point,
    point_to_segment_distance_3d,
    run,
)


def test_forward_model_is_discovered_and_parser_accepts_case_base():
    assert "distance_calculator" in get_forward_models()

    options = build_argument_parser().parse_args(
        ["-c", "distances.yml", "-cn", "model/CASE"]
    )
    assert options.case_name.name == "CASE"
    assert options.egrid is None
    options = build_argument_parser().parse_args(
        ["-c", "distances.yml", "-cn", "model/CASE", "--egrid", "model/OTHER.EGRID"]
    )
    assert options.case_name.name == "CASE"
    assert options.egrid.name == "OTHER.EGRID"


def test_load_config_requires_distance_calculations(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text("distance-calculations: []\n", encoding="utf-8")

    with pytest.raises(ValueError, match="No 'distance_calculations'"):
        load_config(config_path)


def test_load_config_normalizes_hyphenated_keys_and_type(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        "distance-calculations:\n"
        "  - type: polygon-distance\n"
        "    polygon-input: [[0, 0, 0], [1, 0, 0]]\n"
        "    property-threshold: 0.1\n"
        "    output-date: 2040-01-01\n"
        "    unit-conversion: 1000\n"
        "    output-name: distance\n",
        encoding="utf-8",
    )

    calculation = load_config(config_path)["distance_calculations"][0]
    assert calculation["type"] == "polygon_distance"
    assert calculation["polygon_input"] == [[0, 0, 0], [1, 0, 0]]
    assert calculation["property_threshold"] == 0.1
    assert calculation["output_date"].isoformat() == "2040-01-01"
    assert calculation["unit_conversion"] == 1000
    assert calculation["output_name"] == "distance"


def test_load_config_rejects_underscore_keys(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        "distance-calculations:\n"
        "  - type: fault-distance\n"
        "    fault-name: F4\n"
        "    output_date: 2040-01-01\n"
        "    output-name: distance\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must use hyphens instead of underscores"):
        load_config(config_path)


def test_reference_config_covers_all_distance_types():
    config_path = (
        Path(__file__).parents[3]
        / "docs"
        / "reference"
        / "distance_calculator"
        / "config.yml"
    )
    calculations = load_config(config_path)["distance_calculations"]
    required_target_fields = {
        "fault_distance": "fault_name",
        "well_distance": "well_name",
        "polygon_distance": "polygon_input",
    }

    assert {calculation["type"] for calculation in calculations} == set(
        required_target_fields
    )
    for calculation in calculations:
        assert required_target_fields[calculation["type"]] in calculation
        assert calculation["output_name"]


@pytest.mark.parametrize(
    ("aggregation", "expected"),
    [
        ("min", (2, 1.0)),
        ("max", (0, 5.0)),
        ("mean", (None, 3.0)),
        ("median", (None, 3.0)),
    ],
)
def test_aggregate_distance(aggregation, expected):
    assert (
        aggregate_distance([5.0, math.inf, 1.0, 3.0], [0, 1, 2, 3], aggregation)
        == expected
    )


def test_aggregate_distance_excludes_exact_zero():
    assert aggregate_distance([0.0, 2.0], [0, 1], "min") == (1, 2.0)
    assert aggregate_distance([0.0], [0], "min") == (None, None)


@pytest.mark.parametrize(
    ("calculation", "expected"),
    [
        ({}, 1.0),
        ({"unit-conversion": 1000}, 1000.0),
        ({"u": 1000}, 1000.0),
        ({"unit-conversion": None}, 1.0),
    ],
)
def test_resolve_unit_conversion(calculation, expected):
    assert _resolve_unit_conversion(calculation, "distance") == expected


@pytest.mark.parametrize(
    ("calculation", "message"),
    [
        ({"unit-conversion": 0}, "must be non-zero"),
        ({"unit-conversion": "invalid"}, "must be numeric"),
        ({"unit-conversion": 1, "u": 1}, "use either"),
    ],
)
def test_resolve_unit_conversion_rejects_invalid_values(calculation, message):
    with pytest.raises(ValueError, match=message):
        _resolve_unit_conversion(calculation, "distance")


def test_polygon_point_and_segment_distance():
    assert parse_polygon_point("1, 2, 3") == (1.0, 2.0, 3.0)
    assert (
        point_to_segment_distance_3d((1.0, 2.0, 0.0), (0.0, 0.0, 0.0), (3.0, 0.0, 0.0))
        == 2.0
    )


def test_fault_distance_uses_generated_resinsight_property_and_excludes_zero(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        distance_tasks,
        "rips",
        SimpleNamespace(PropertyType=SimpleNamespace(GENERATED="generated")),
    )
    centers = [
        SimpleNamespace(x=0.0, y=0.0, z=0.0),
        SimpleNamespace(x=1.0, y=0.0, z=0.0),
    ]
    grid = SimpleNamespace(
        dimensions=lambda: SimpleNamespace(i=2, j=1, k=1),
        cell_centers=lambda: centers,
    )
    fault = SimpleNamespace(fault_name="F4")
    fault_collection = SimpleNamespace(faults=lambda: [fault])
    view = SimpleNamespace(
        fault_collection=lambda: fault_collection,
        add_fault_distance=lambda _name, _faults: SimpleNamespace(
            result_name="F4_DISTANCE"
        ),
    )
    case = SimpleNamespace(
        views=lambda: [view],
        grid=lambda _index: grid,
        cell_info_for_active_cells=lambda: [
            SimpleNamespace(grid_index=0, local_ijk=SimpleNamespace(i=index, j=0, k=0))
            for index in range(2)
        ],
        time_steps=lambda: [date(2040, 1, 1)],
        grid_property=lambda *_args: [0.0, 1.0],
    )

    assert (
        run(
            {
                "distance_calculations": [
                    {
                        "type": "fault_distance",
                        "fault_name": "F4",
                        "output_name": "F4_DISTANCE",
                    }
                ]
            },
            case,
        )
        == 0
    )
    assert (tmp_path / "F4_DISTANCE").read_text() == "1\n"


def test_well_distance_uses_connected_cells_and_excludes_zero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    centers = [
        SimpleNamespace(x=0.0, y=0.0, z=0.0),
        SimpleNamespace(x=5.0, y=0.0, z=0.0),
    ]
    grid = SimpleNamespace(
        dimensions=lambda: SimpleNamespace(i=2, j=1, k=1),
        cell_centers=lambda: centers,
    )
    connection = SimpleNamespace(grid_index=0, ijk=SimpleNamespace(i=1, j=0, k=0))
    well = SimpleNamespace(name="LEG_1", cells=lambda _time_step: [connection])
    case = SimpleNamespace(
        grid=lambda _index: grid,
        cell_info_for_active_cells=lambda: [
            SimpleNamespace(grid_index=0, local_ijk=SimpleNamespace(i=index, j=0, k=0))
            for index in range(2)
        ],
        simulation_wells=lambda: [well],
        time_steps=lambda: [date(2040, 1, 1)],
    )

    assert (
        run(
            {
                "distance_calculations": [
                    {
                        "type": "well_distance",
                        "well_name": "LEG_1",
                        "output_name": "LEG_1_DISTANCE",
                    }
                ]
            },
            case,
        )
        == 0
    )
    assert (tmp_path / "LEG_1_DISTANCE").read_text() == "5\n"


@pytest.mark.parametrize(
    ("printing_distance_map", "unit_conversion", "expected_map", "expected_scalar"),
    [
        (None, None, False, "1\n"),
        (True, None, True, "1\n"),
        (True, 0.5, True, "2\n"),
    ],
)
def test_run_defaults_aggregation_and_distance_map(
    tmp_path,
    monkeypatch,
    printing_distance_map,
    unit_conversion,
    expected_map,
    expected_scalar,
):
    monkeypatch.chdir(tmp_path)
    centers = [
        SimpleNamespace(x=1.0, y=2.0, z=0.0),
        SimpleNamespace(x=2.0, y=1.0, z=0.0),
    ]
    grid = SimpleNamespace(
        dimensions=lambda: SimpleNamespace(i=2, j=1, k=1),
        cell_centers=lambda: centers,
    )
    case = SimpleNamespace(
        grid=lambda _index: grid,
        cell_info_for_active_cells=lambda: [
            SimpleNamespace(grid_index=0, local_ijk=SimpleNamespace(i=index, j=0, k=0))
            for index in range(2)
        ],
        time_steps=lambda: [date(2040, 1, 1)],
    )
    calculation = {
        "type": "polygon_distance",
        "polygon_input": [[0, 0, 0], [3, 0, 0]],
        "output_name": "P1_POLYGON_DISTANCE",
    }
    if printing_distance_map is not None:
        calculation["printing_distance_map"] = printing_distance_map
    if unit_conversion is not None:
        calculation["unit-conversion"] = unit_conversion
    config = {"distance_calculations": [calculation]}

    assert run(config, case) == 0
    assert (tmp_path / "P1_POLYGON_DISTANCE").read_text() == expected_scalar
    map_path = tmp_path / "P1_POLYGON_DISTANCE_map"
    assert map_path.exists() is expected_map
    if expected_map:
        map_text = map_path.read_text()
        assert map_text.startswith("P1_POLYGON_DISTANCE\n")
        assert map_text.endswith("/\n")
        map_values = [float(value) for value in map_text.split()[1:-1]]
        conversion = unit_conversion or 1.0
        assert map_values == [2.0 / conversion, 1.0 / conversion]


@pytest.mark.parametrize(
    ("output_date", "expected_distance", "expected_cell_count", "expected_scope"),
    [
        (None, "1\n", 2, "all timesteps"),
        ("2040-01-01", "2\n", 1, "2040-01-01"),
    ],
)
def test_output_date_controls_timestep_filter(
    tmp_path,
    monkeypatch,
    capsys,
    output_date,
    expected_distance,
    expected_cell_count,
    expected_scope,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        distance_tasks,
        "rips",
        SimpleNamespace(PropertyType=SimpleNamespace(DYNAMIC_NATIVE="dynamic")),
    )
    centers = [
        SimpleNamespace(x=1.0, y=2.0, z=0.0),
        SimpleNamespace(x=2.0, y=1.0, z=0.0),
    ]
    grid = SimpleNamespace(
        dimensions=lambda: SimpleNamespace(i=2, j=1, k=1),
        cell_centers=lambda: centers,
    )
    values_by_timestep = [[0.2, 0.0], [0.0, 0.2]]
    case = SimpleNamespace(
        grid=lambda _index: grid,
        cell_info_for_active_cells=lambda: [
            SimpleNamespace(grid_index=0, local_ijk=SimpleNamespace(i=index, j=0, k=0))
            for index in range(2)
        ],
        time_steps=lambda: [date(2040, 1, 1), date(2041, 1, 1)],
        grid_property=lambda _kind, _keyword, timestep, _grid: values_by_timestep[
            timestep
        ],
    )
    config = {
        "distance_calculations": [
            {
                "type": "polygon_distance",
                "polygon_input": [[0, 0, 0], [3, 0, 0]],
                "property": "sgas",
                "property_threshold": 0.1,
                "aggregation": "min",
                "output_name": "P1_POLYGON_DISTANCE",
                "printing_distance_map": False,
            }
        ]
    }
    if output_date is not None:
        config["distance_calculations"][0]["output_date"] = output_date

    assert run(config, case) == 0
    assert (tmp_path / "P1_POLYGON_DISTANCE").read_text() == expected_distance
    assert (
        f"SGAS >= 0.1 @ {expected_scope} ({expected_cell_count} cells)"
        in capsys.readouterr().out
    )
