import math
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from ruamel.yaml import YAML

from everest_models.forward_models import get_forward_models
from everest_models.jobs.fm_distance_calculator import tasks as distance_tasks
from everest_models.jobs.fm_distance_calculator.cli import load_config
from everest_models.jobs.fm_distance_calculator.config_model import (
    DistanceConfig,
    PolygonCalculation,
)
from everest_models.jobs.fm_distance_calculator.parser import build_argument_parser
from everest_models.jobs.fm_distance_calculator.tasks import (
    aggregate_distance,
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

    with pytest.raises(ValidationError, match="at least 1 item"):
        load_config(config_path)


def test_load_config_validates_nested_property_and_polygon_points(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        "distance-calculations:\n"
        "  - type: polygon\n"
        "    points: [[0, 0, 0], [1, 0, 0]]\n"
        "    property:\n"
        "      name: sgas\n"
        "      threshold: 0.1\n"
        "      date: 2040-01-01\n"
        "    multiplier: 0.001\n"
        "    output: distance\n",
        encoding="utf-8",
    )

    calculation = load_config(config_path).distance_calculations[0]
    assert isinstance(calculation, PolygonCalculation)
    assert calculation.points == ((0, 0, 0), (1, 0, 0))
    assert calculation.property is not None
    assert calculation.property.date == date(2040, 1, 1)


@pytest.mark.parametrize(
    ("fields", "error"),
    [
        pytest.param({"type": "well-distance"}, "union_tag_invalid", id="old-type"),
        pytest.param({"unit-conversion": 1000}, "extra_forbidden", id="old-unit"),
        pytest.param({"name": ""}, "string_too_short", id="empty-name"),
        pytest.param({"aggregation": "sum"}, "literal_error", id="aggregation"),
        pytest.param({"property": "sgas"}, "model_type", id="old-property"),
        pytest.param(
            {"property": {"name": ["sgas"]}}, "string_type", id="property-list"
        ),
        pytest.param(
            {"property": {"name": "sgas, swat"}},
            "string_pattern_mismatch",
            id="comma-separated-properties",
        ),
        pytest.param(
            {"property": {"name": "sgas", "threshold": [0.1]}},
            "float_type",
            id="threshold-list",
        ),
        pytest.param(
            {"property": {"name": "sgas", "date": ["2040-01-01"]}},
            "value_error",
            id="date-list",
        ),
        pytest.param(
            {"property": {"name": "sgas", "date": "2040-02-31"}},
            "date_from_datetime_parsing",
            id="invalid-date",
        ),
        pytest.param({"verbose": "true"}, "bool_type", id="verbose-string"),
        pytest.param({"multiplier": 0}, "value_error", id="zero-multiplier"),
        pytest.param(
            {"multiplier": math.inf}, "finite_number", id="infinite-multiplier"
        ),
    ],
)
def test_config_rejects_invalid_calculation_fields(fields, error):
    calculation = {"type": "well", "name": "PROD", "output": "distance", **fields}

    with pytest.raises(ValidationError) as exc_info:
        DistanceConfig.model_validate({"distance-calculations": [calculation]})

    assert exc_info.value.errors()[0]["type"] == error


@pytest.mark.parametrize("points", [[[0, 0, 0]], [[0, 0], [1, 0, 0]]])
def test_config_requires_at_least_two_3d_polygon_points(points):
    calculation = {"type": "polygon", "points": points, "output": "distance"}
    with pytest.raises(ValidationError, match="points"):
        DistanceConfig.model_validate({"distance-calculations": [calculation]})


def test_model_schema_shows_all_calculation_types():
    schema = DistanceConfig.commented_map(minimal=False)
    calculations = schema["distance-calculations"]
    assert [calculation["type"] for calculation in calculations] == [
        "fault",
        "well",
        "polygon",
    ]
    assert calculations[0]["property"]["threshold"] == 0.0
    assert len(calculations[2]["points"]) == 2


def test_reference_schema_matches_model(reference_docs):
    schema_path = reference_docs / "distance_calculator" / "config.yml"
    schema = YAML(typ="safe").load(schema_path)

    assert schema == DistanceConfig.commented_map(minimal=False)


def test_reference_config_covers_all_distance_types():
    config_path = (
        Path(__file__).parents[3]
        / "docs"
        / "reference"
        / "distance_calculator"
        / "example.yml"
    )
    calculations = load_config(config_path).distance_calculations
    assert {calculation.type for calculation in calculations} == {
        "fault",
        "well",
        "polygon",
    }


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


def test_point_to_segment_distance():
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
            DistanceConfig.model_validate(
                {
                    "distance-calculations": [
                        {
                            "type": "fault",
                            "name": "F4",
                            "output": "F4_DISTANCE",
                        }
                    ]
                }
            ),
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
            DistanceConfig.model_validate(
                {
                    "distance-calculations": [
                        {
                            "type": "well",
                            "name": "LEG_1",
                            "output": "LEG_1_DISTANCE",
                        }
                    ]
                }
            ),
            case,
        )
        == 0
    )
    assert (tmp_path / "LEG_1_DISTANCE").read_text() == "5\n"


@pytest.mark.parametrize(
    ("default_verbose", "calculation_options", "expected_map", "expected_scalar"),
    [
        pytest.param({}, {}, False, "1\n", id="default-no-map"),
        pytest.param(
            {"verbose": True}, {"multiplier": 2}, True, "2\n", id="inherit-and-multiply"
        ),
        pytest.param(
            {"verbose": True}, {"verbose": False}, False, "1\n", id="disable-map"
        ),
        pytest.param({}, {"verbose": True}, True, "1\n", id="enable-map"),
    ],
)
def test_run_defaults_aggregation_and_distance_map(
    tmp_path,
    monkeypatch,
    default_verbose,
    calculation_options,
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
        "type": "polygon",
        "points": [[0, 0, 0], [3, 0, 0]],
        "output": "P1_POLYGON_DISTANCE",
        **calculation_options,
    }
    config = DistanceConfig.model_validate(
        {"distance-calculations": [calculation], **default_verbose}
    )

    assert run(config, case) == 0
    assert (tmp_path / "P1_POLYGON_DISTANCE").read_text() == expected_scalar
    map_path = tmp_path / "P1_POLYGON_DISTANCE_map"
    assert map_path.exists() is expected_map
    if expected_map:
        map_text = map_path.read_text()
        assert map_text.startswith("P1_POLYGON_DISTANCE\n")
        assert map_text.endswith("/\n")
        map_values = [float(value) for value in map_text.split()[1:-1]]
        multiplier = calculation_options.get("multiplier", 1.0)
        assert map_values == [2.0 * multiplier, multiplier]


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
    config = DistanceConfig.model_validate(
        {
            "distance-calculations": [
                {
                    "type": "polygon",
                    "points": [[0, 0, 0], [3, 0, 0]],
                    "property": {"name": "sgas", "threshold": 0.1, "date": output_date},
                    "output": "P1_POLYGON_DISTANCE",
                }
            ]
        }
    )

    assert run(config, case) == 0
    assert (tmp_path / "P1_POLYGON_DISTANCE").read_text() == expected_distance
    assert (
        f"SGAS >= 0.1 @ {expected_scope} ({expected_cell_count} cells)"
        in capsys.readouterr().out
    )
