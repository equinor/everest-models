import json

import ruamel.yaml as yaml
from configsuite import ConfigSuite
from utils import relpath, tmpdir

from spinningjenny.jobs.fm_add_templates.schemas import build_schema
from spinningjenny.jobs.fm_add_templates.tasks import add_templates

TEST_DATA_PATH = relpath("tests", "testdata", "add_tmpl")


@tmpdir(TEST_DATA_PATH)
def test_add_templates(capsys):
    # Load input well operations file
    with open("wells.json", "r") as f:
        wells = json.load(f)

    # Load config
    with open("config.yml", "r") as f:
        config = ConfigSuite(
            yaml.YAML(typ="safe", pure=True).load(f),
            build_schema(),
            deduce_required=True,
        )

    # Check loaded config is valid
    assert config.valid

    output, warnings, _ = add_templates(
        templates=config.snapshot.templates, wells=wells
    )

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
    _, _, errors = add_templates(templates=config.snapshot.templates, wells=wells)

    assert len(errors) == 1, "There should be only one error"

    assert (
        "No template matched for well:'w_test' operation:'oepn' at date:'2001-02-11'"
        in errors
    )
