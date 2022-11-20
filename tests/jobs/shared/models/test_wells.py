import datetime
import pathlib
from typing import Dict

import pytest
from pydantic import ValidationError

from spinningjenny.jobs.shared.models import WellListModel
from spinningjenny.jobs.shared.models.wells import Operation, WellModel


@pytest.fixture(scope="module")
def well_dict(path_test_data) -> Dict:
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
    return WellListModel.parse_obj(well_dict)


def test_well_model_fields(well_model):
    assert isinstance(well_model.__root__, tuple)
    well = well_model[0]
    assert isinstance(well, WellModel)
    assert isinstance(well.name, str)
    assert well.name == "WELL1"
    with pytest.raises(TypeError, match="allow_mutation set to False"):
        well.name = "should not work"
    assert isinstance(well.readydate, datetime.date)
    assert isinstance(well.completion_date, datetime.date)
    assert isinstance(well.drill_time, int)
    assert isinstance(well.ops, tuple)
    op1 = well.ops[0]
    assert isinstance(op1, Operation)
    assert isinstance(op1.date, datetime.date)
    assert isinstance(op1.opname, str)
    assert isinstance(op1.template, pathlib.Path)
    ops2 = well_model[1].ops
    with pytest.raises(ValidationError):
        ops2[0].template = "does_not_exist.txt"  # file does not exist
        ops2[0].template = "src"  # not a file
    assert isinstance(ops2[1].phase, str)
    assert isinstance(ops2[1].rate, float)


def test_well_model_minimum_fields():
    assert not WellListModel.parse_obj([])  # does not throw error
    assert WellListModel.parse_obj([dict(name="WELL", drill_time=23)])


def test_well_model_is_subscribable(well_model):
    wells = WellListModel.parse_obj([])
    assert not wells.__root__
    assert len([well for well in wells]) == 0
    assert well_model[1]


def test_well_model_to_dict(well_model):
    well_dict = well_model.to_dict()
    assert tuple(well_dict.keys()) == ("WELL1", "INJECT1")
    for index, (name, value) in enumerate(well_dict.items()):
        assert name == value.name
        assert isinstance(value, WellModel)
        assert well_model[index] == value


def test_well_model_missing_templates(well_model):
    assert not tuple(well_model[0].missing_templates())
    assert tuple(well_model[1].missing_templates()) == (
        ("open", datetime.date.fromisoformat("2019-05-12")),
        ("rate", datetime.date.fromisoformat("2019-07-01")),
        ("rate", datetime.date.fromisoformat("2019-08-30")),
        ("rate", datetime.date.fromisoformat("2019-11-08")),
    )