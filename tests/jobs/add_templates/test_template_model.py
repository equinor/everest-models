import pathlib
from copy import deepcopy

import pytest
from pydantic import ValidationError
from sub_testdata import ADD_TEMPLATE as TEST_DATA

from everest_models.jobs.fm_add_templates.config_model import (
    Keys,
    Template,
    TemplateConfig,
)
from everest_models.jobs.shared.models import Operation, PhaseEnum


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
    assert isinstance(template.keys, dict)
    assert isinstance(template.keys["opname"], str)
    assert isinstance(add_tmpl_config.templates[3].keys["phase"], PhaseEnum)

    with pytest.raises(ValidationError, match="Instance is frozen"):
        add_tmpl_config.templates = ()
        template.file = "does_not_exist.txt"
        template.keys = Keys(opname="str")
        template.keys["opname"] = "str"


def test_template_model_minimum_fields(template_dict):
    assert TemplateConfig.model_validate(template_dict)
    with pytest.raises(ValidationError, match="Field required"):
        TemplateConfig.model_validate({})


def test_template_model_file(template_dict):
    template_dict = deepcopy(template_dict)
    template_dict["templates"][0]["file"] = "does_not_exist.txt"
    with pytest.raises(ValidationError, match="does not point to a file"):
        TemplateConfig.model_validate(template_dict)


def test_key_equal_operator(template_dict):
    template = TemplateConfig.model_validate(template_dict).templates[0]
    op = Operation(date="2000-12-23", opname="open")
    assert template.matching_keys(op)
    op.tokens["rate"] = 2.0
    assert template.matching_keys(op)
    op.tokens["phase"] = "water"
    assert not template.matching_keys(op)
