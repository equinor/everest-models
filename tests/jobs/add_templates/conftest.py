import pytest
from sub_testdata import ADD_TEMPLATE as TEST_DATA

from spinningjenny.jobs.fm_add_templates.template_model import TemplateConfigModel
from spinningjenny.jobs.shared.validators import parse_file


@pytest.fixture()
def add_tmpl_config(copy_testdata_tmpdir) -> TemplateConfigModel:
    copy_testdata_tmpdir(TEST_DATA)
    return parse_file("config.yml", TemplateConfigModel)
