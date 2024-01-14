import datetime
import pathlib
from typing import Any, Dict, List

import pytest
from everest_models.jobs.shared.models import Operation, PhaseEnum, Well, Wells
from pydantic import ValidationError


@pytest.fixture(scope="module")
def well_dict(path_test_data) -> List[Dict[str, Any]]:
    template_file = "add_tmpl/templates/template_{tmpl}.tmpl"
    return [
        {
            "drill_time": 50,
            "name": "WELL1",
            "readydate": "2022-12-01",
            "completion_date": "2022-12-01",
            "ops": [
                {
                    "opname": "open",
                    "template": path_test_data / template_file.format(tmpl="open"),
                    "date": "2022-12-01",
                }
            ],
        },
        {
            "name": "INJECT1",
            "drill_time": 27,
            "readydate": "2019-05-12",
            "ops": [
                {"opname": "open", "date": "2019-05-12"},
                {
                    "opname": "rate",
                    "phase": "water",
                    "rate": 600.0,
                    "date": "2019-05-12",
                    "template": path_test_data
                    / template_file.format(tmpl="rate_inject"),
                },
                {"opname": "rate", "phase": "gas", "rate": 400.0, "date": "2019-07-01"},
                {"opname": "rate", "phase": "gas", "rate": 200.0, "date": "2019-08-30"},
                {"opname": "rate", "phase": "water", "rate": 333, "date": "2019-11-08"},
            ],
        },
    ]


@pytest.fixture(scope="module")
def well_model(well_dict):
    return Wells.model_validate(well_dict)


def test_operation_model_field():
    data = {
        "date": "2019-09-15",
        "opname": "open",
        "tokens": {"s": 12, "phase": "water"},
    }
    operation = Operation.model_validate(data)
    assert operation
    assert isinstance(operation.tokens.get("phase"), PhaseEnum)
    with pytest.raises(ValidationError):
        Operation.model_validate({"z": 3.3, **data})


def test_well_model_fields(well_model):
    assert isinstance(well_model.root, tuple)
    well = well_model[0]
    assert isinstance(well, Well)
    assert isinstance(well.name, str)
    assert well.name == "WELL1"
    with pytest.raises(ValidationError, match="Field is frozen"):
        well.name = "should not work"
    assert isinstance(well.readydate, datetime.date)
    assert isinstance(well.completion_date, datetime.date)
    assert isinstance(well.drill_time, int)
    assert isinstance(well.operations, tuple)
    operation = well.operations[0]
    assert isinstance(operation, Operation)
    assert isinstance(operation.date, datetime.date)
    assert isinstance(operation.opname, str)
    assert isinstance(operation.template, pathlib.Path)
    operation_2 = well_model[1].operations
    with pytest.raises(ValidationError):
        operation_2[0].template = "does_not_exist.txt"  # file does not exist
        operation_2[0].template = "src"  # not a file
    assert isinstance(operation_2[1].tokens["phase"], PhaseEnum)
    assert isinstance(operation_2[1].tokens["rate"], float)


def test_well_model_minimum_fields():
    assert not Wells.model_validate([]).root  # does not throw error
    assert Wells.model_validate([{"name": "WELL", "drill_time": 23}])


def test_well_model_is_subscribable(well_model):
    wells = Wells.model_validate([])
    assert not wells.root
    assert not list(wells)
    assert well_model[1]


def test_well_model_to_dict(well_model):
    well_dict = well_model.to_dict()
    assert tuple(well_dict.keys()) == ("WELL1", "INJECT1")
    for index, (name, value) in enumerate(well_dict.items()):
        assert name == value.name
        assert isinstance(value, Well)
        assert well_model[index] == value


def test_legacy_well_model_missing_templates(well_model):
    assert not tuple(well_model[0].missing_templates)
    assert tuple(well_model[1].missing_templates) == (
        ("open", datetime.date.fromisoformat("2019-05-12")),
        ("rate", datetime.date.fromisoformat("2019-07-01")),
        ("rate", datetime.date.fromisoformat("2019-08-30")),
        ("rate", datetime.date.fromisoformat("2019-11-08")),
    )
