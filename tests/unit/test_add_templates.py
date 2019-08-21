from __future__ import absolute_import
import json
import yaml
import pytest

from configsuite import ConfigSuite

from tests import tmpdir, relpath
from spinningjenny.script.fm_add_templates import main_entry_point
from spinningjenny.add_templates.add_templates_job import add_templates
from spinningjenny.add_templates.add_tmpl_schema import build_schema

TEST_DATA_PATH = relpath("tests", "testdata", "add_tmpl")


@tmpdir(TEST_DATA_PATH)
def test_add_templates():
    # Load input well operations file
    with open("wells.json", "r") as f:
        wells = json.load(f)

    # Load config
    with open("config.yml", "r") as f:
        config = ConfigSuite(yaml.safe_load(f), build_schema())

    # Check loaded config is valid
    assert config.valid

    output, warnings = add_templates(templates=config.snapshot.templates, wells=wells)

    with open("expected_out.json", "r") as input_file:
        expected_result = json.load(input_file)

    assert output == expected_result

    assert len(warnings) == 1, "There should be only one warning"

    assert "./templates/notused.tmpl" in next(iter(warnings))

    # Add well containing well operation that doesn't match any key set asociated
    # with a template in the config
    wells.append(
        {
            "readydate": "2001-06-11",
            "name": "w_test",
            "ops": [{"date": "2001-02-11", "opname": "oepn"}],
        }
    )
    _, warnings = add_templates(templates=config.snapshot.templates, wells=wells)
    # Check one extra warning is generated for the new input
    assert len(warnings) == 2, "There should be two warnings now!"
    # Check the extra warning is the one we expect
    assert (
        "No template matched for well:'w_test' operation:'oepn' at date:'2001-02-11'"
        in warnings
    )
