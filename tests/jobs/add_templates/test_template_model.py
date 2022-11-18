import pathlib
from copy import deepcopy

import pytest
from pydantic import ValidationError
from sub_testdata import ADD_TEMPLATE as TEST_DATA

from spinningjenny.jobs.fm_add_templates.template_model import (
    Key,
    Template,
    TemplateConfigModel,
)
from spinningjenny.jobs.shared.models import Operation


@pytest.fixture(scope="module")
def template_dict(path_test_data):
    return {
        "templates": [
            {
                "file": path_test_data / f"{TEST_DATA}/templates/template_open.tmpl",
                "keys": {
                    "opname": "open",
                },
            },
        ],
    }


def test_template_model_fields(add_tmpl_config):
    assert isinstance(add_tmpl_config.templates, tuple)
    template = add_tmpl_config.templates[0]
    assert isinstance(template, Template)
    assert isinstance(template.file, pathlib.Path)
    assert isinstance(template.keys, Key)
    assert isinstance(template.keys.opname, str)
    assert isinstance(add_tmpl_config.templates[3].keys.phase, str)

    with pytest.raises(TypeError, match="allow_mutation set to False"):
        template.file = "does_not_exist.txt"
        template.keys = Key(opname="str")

    with pytest.raises(TypeError, match="immutable"):
        add_tmpl_config.templates = ()
        template.keys.opname = "str"
        template.keys.phase = "str"

    assert isinstance(template.is_utilized, bool)
    assert not template.is_utilized
    template.is_utilized = True
    assert template.is_utilized


def test_template_model_minimum_fields(template_dict):
    assert TemplateConfigModel.parse_obj(template_dict)
    with pytest.raises(ValidationError, match="field required"):
        TemplateConfigModel.parse_obj({})


def test_template_model_file(template_dict):
    template_dict = deepcopy(template_dict)
    template_dict["templates"][0]["file"] = "does_not_exist.txt"
    with pytest.raises(ValidationError, match="does not exist"):
        TemplateConfigModel.parse_obj(template_dict)
    template_dict["templates"][0]["file"] = pathlib.Path().parent
    with pytest.raises(ValidationError, match="does not point to a file"):
        TemplateConfigModel.parse_obj(template_dict)


def test_key_equal_operator(template_dict):
    templates = TemplateConfigModel.parse_obj(template_dict)
    keys = templates.templates[0].keys
    assert keys == Key(opname="open")
    assert keys != Key(opname="not_open")
    assert keys != Key(opname="open", phase="water")
    op = Operation(date="2000-12-23", opname="open")
    assert keys == op
    op.rate = 2.0
    assert keys == op
    op.phase = "water"
    assert keys != op
