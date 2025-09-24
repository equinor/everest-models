import sys
from pathlib import Path

import pytest
from ert import ForwardModelStepPlugin
from ert.config import ErtConfig
from pydantic import BaseModel, ConfigDict
from ruamel.yaml import YAML
from sub_testdata import ADD_TEMPLATE as TEST_DATA

from everest_models.forward_models import (
    build_forward_model_step_plugin,
    get_forward_models,
)
from everest_models.jobs.fm_add_templates.config_model import TemplateConfig

FORWARD_MODEL_DIR = "forward_models"


def test_hooks_registered(plugin_manager):
    assert sys.modules["everest_models.everest_hooks"] in plugin_manager.get_plugins()


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


@pytest.mark.parametrize(
    ["fm_steps", "expected_error"],
    [
        (
            [
                "well_constraints   -c files/wc_config.yml -rc well_rate.json -o out1",
            ],
            "fm_well_constraints: error: the following arguments are required: -i/--input",
        ),
        (
            [
                "not_add_templates     -i wc_wells.json -c files/at_config.yml -o out2",
                "schmerge           -i at_wells.json -o out3",
                "rf -s TEST -o out4",
            ],
            "fm_schmerge: error: the following arguments are required: -s/--schedule",
        ),
        (
            ["well_trajectory  -E eclipse/config/path"],
            "fm_well_trajectory: error: the following arguments are required: -c/--config",
        ),
        ([], ""),
    ],
)
def test_valid_fm_step_args(fm_steps, expected_error, plugin_manager, capsys):
    if expected_error:
        with pytest.raises(SystemExit):
            plugin_manager.hook.check_forward_model_arguments(
                forward_model_steps=fm_steps
            )
        assert expected_error in capsys.readouterr().err
    else:
        plugin_manager.hook.check_forward_model_arguments(forward_model_steps=fm_steps)


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
        YAML(typ="safe", pure=True).dump({"content": "good"}, fd)
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


def test_build_forward_model_step_plugin():
    expected_names = get_forward_models()
    expected_fm_names = [f"fm_{name}" for name in expected_names]

    fm_steps_instances = [
        build_forward_model_step_plugin(fm_name)() for fm_name in get_forward_models()
    ]

    executables = [instance.executable for instance in fm_steps_instances]
    names = [instance.name for instance in fm_steps_instances]

    assert executables == expected_fm_names
    assert names == expected_names


def test_everest_models_jobs():
    jobs = get_forward_models()
    assert bool(jobs)
    for job in jobs:
        job_class = ErtConfig.with_plugins().PREINSTALLED_FORWARD_MODEL_STEPS.get(job)
        assert job_class is not None
        assert isinstance(job_class, ForwardModelStepPlugin)
