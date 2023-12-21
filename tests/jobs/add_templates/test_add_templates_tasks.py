import logging

from everest_models.jobs.fm_add_templates.config_model import Template
from everest_models.jobs.fm_add_templates.tasks import add_templates, collect_matching
from everest_models.jobs.shared.models import Operation, WellConfig
from everest_models.jobs.shared.validators import parse_file
from sub_testdata import ADD_TEMPLATE as TEST_DATA


def test_collect_matching(add_tmpl_config):
    wells = parse_file("wells.json", WellConfig)
    expected = {
        "w1": ["templates/template_open.tmpl"],
        "w2": [
            "templates/template_open.tmpl",
            "templates/template_water_inject.tmpl",
            "templates/template_oil_prod.tmpl",
            "templates/template_water_inject.tmpl",
            "templates/template_rate_inject.tmpl",
        ],
        "w3": ["templates/template_open.tmpl", "templates/template_water_inject.tmpl"],
        "w4": [
            "templates/template_open.tmpl",
            "templates/template_oil_prod.tmpl",
            "templates/template_water_inject.tmpl",
        ],
        "w5": ["templates/template_open.tmpl"],
    }
    assert all(
        str(template.file) in expected[well_name] and template.matching_keys(op)
        for well_name, op, template in collect_matching(
            templates=add_tmpl_config.templates, wells=wells
        )
    )


def test_add_templates(path_test_data, caplog):
    template_path = path_test_data / f"{TEST_DATA}/templates/template_open.tmpl"
    template = Template(**{"file": template_path, "keys": {"opname": "tester"}})
    operation = Operation(**{"date": "2020-12-12", "opname": "tester"})
    assert operation.template is None

    consumed = add_templates(well_name="t1", operation=operation, template=template)
    assert operation.template == template_path == consumed

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelno == logging.INFO
    assert (
        record.message
        == f"Template '{template_path}' was inserted for well 't1' date '2020-12-12' operation 'tester'"
    )
