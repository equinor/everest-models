import itertools
import sys
from pathlib import Path

import pytest
import ruamel.yaml as yaml
from everest_models.jobs.fm_add_templates.config_model import TemplateConfig
from pydantic import BaseModel, ConfigDict
from sub_testdata import ADD_TEMPLATE as TEST_DATA

FORWARD_MODEL_DIR = "forward_models"


def test_hooks_registered(plugin_manager):
    assert sys.modules["everest_models.everest_hooks"] in plugin_manager.get_plugins()


def test_get_forward_models_hook(plugin_manager):
    jobs = {
        "stea": f"{FORWARD_MODEL_DIR}/stea",
        "drill_planner": f"{FORWARD_MODEL_DIR}/drill_planner",
        "compute_economics": f"{FORWARD_MODEL_DIR}/compute_economics",
        "schmerge": f"{FORWARD_MODEL_DIR}/schmerge",
        "extract_summary_data": f"{FORWARD_MODEL_DIR}/extract_summary_data",
        "drill_date_planner": f"{FORWARD_MODEL_DIR}/drill_date_planner",
        "strip_dates": f"{FORWARD_MODEL_DIR}/strip_dates",
        "select_wells": f"{FORWARD_MODEL_DIR}/select_wells",
        "npv": f"{FORWARD_MODEL_DIR}/npv",
        "well_constraints": f"{FORWARD_MODEL_DIR}/well_constraints",
        "add_templates": f"{FORWARD_MODEL_DIR}/add_templates",
        "rf": f"{FORWARD_MODEL_DIR}/rf",
        "well_filter": f"{FORWARD_MODEL_DIR}/well_filter",
        "interpret_well_drill": f"{FORWARD_MODEL_DIR}/interpret_well_drill",
        "well_trajectory": f"{FORWARD_MODEL_DIR}/well_trajectory",
        "well_swapping": f"{FORWARD_MODEL_DIR}/well_swapping",
    }
    assert all(
        jobs[job["name"]] in job["path"]
        for job in itertools.chain.from_iterable(
            plugin_manager.hook.get_forward_models()
        )
    )


def test_get_forward_model_schemas_hook(plugin_manager):
    assert not set(plugin_manager.hook.get_forward_models_schemas().pop()) - {
        "add_templates",
        "compute_economics",
        "drill_planner",
        "npv",
        "well_trajectory",
        "well_constraints",
        "well_swapping",
    }


def test_get_forward_model_schemas_hook_keys_are_options(plugin_manager):
    assert all(
        schema is not None
        for job, schema in plugin_manager.hook.get_forward_models_schemas()
        .pop()
        .items()
        if job != "select_wells"
    )


class SchemaModel(BaseModel):
    content: str
    model_config = ConfigDict(extra="forbid")


def test_parse_forward_model_schema_hook(switch_cwd_tmp_path, plugin_manager):
    path = "config.yml"
    with open(path, "w") as fd:
        yaml.YAML(typ="safe", pure=True).dump({"content": "good"}, fd)
    assert plugin_manager.hook.parse_forward_model_schema(
        path=path,
        schema=SchemaModel,
    )


@pytest.mark.parametrize(
    "job, config_file",
    (pytest.param("well_swapping", "well_swap_config.yml", id="well_swapping"),),
)
def test_lint_forward_model_hook(
    job: str, config_file: str, path_test_data: Path, plugin_manager
):
    assert not plugin_manager.hook.lint_forward_model(
        job=job, args=("--config", str(path_test_data / job / config_file))
    ).pop()


@pytest.mark.parametrize(
    "job",
    (
        "stea",
        "drill_planner",
        "compute_economics",
        "schmerge",
        "extract_summary_data",
        "drill_date_planner",
        "strip_dates",
        "select_wells",
        "npv",
        "well_constraints",
        "add_templates",
        "rf",
        "well_filter",
        "interpret_well_drill",
        "well_trajectory",
    ),
)
def test_lint_forward_model_hook_not_implemented(job: str, plugin_manager):
    with pytest.raises((AttributeError, ModuleNotFoundError)):
        assert not plugin_manager.hook.lint_forward_model(
            job=job, args=("--config", "something")
        ).pop()


def test_multi_hook_calls(copy_testdata_tmpdir, plugin_manager):
    copy_testdata_tmpdir(TEST_DATA)
    schema = plugin_manager.hook.get_forward_models_schemas()[0]["add_templates"]
    assert schema == TemplateConfig
    assert isinstance(
        plugin_manager.hook.parse_forward_model_schema(
            path="config.yml",
            schema=schema,
        ).pop(),
        schema,
    )
