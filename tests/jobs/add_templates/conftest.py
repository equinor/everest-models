import pytest
from sub_testdata import ADD_TEMPLATE as TEST_DATA

from everest_models.jobs.fm_add_templates.config_model import TemplateConfig
from everest_models.jobs.shared.validators import parse_file


@pytest.fixture()
def add_tmpl_config(copy_testdata_tmpdir) -> TemplateConfig:
    copy_testdata_tmpdir(TEST_DATA)
    return parse_file("config.yml", TemplateConfig)
