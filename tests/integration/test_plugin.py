import itertools
import re
import sys

import pytest
import ruamel.yaml as yaml
from pydantic import BaseModel, Extra
from everest_models.jobs.fm_add_templates.config_model import TemplateConfig
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
    }
    assert all(
        jobs[job["name"]] in job["path"]
        for job in itertools.chain.from_iterable(
            plugin_manager.hook.get_forward_models()
        )
    )


def test_get_forward_model_schemas_hook(plugin_manager):
    assert not set(plugin_manager.hook.get_forward_models_schemas()[0]) - {
        "add_templates",
        "drill_planner",
        "npv",
        "well_trajectory",
        "well_constraints",
    }


def test_get_forward_model_schemas_hook_keys_are_options(plugin_manager):
    assert all(
        re.match(r"^-\w{1,3}/-(-\w+)*$", option)
        for job, schemas in plugin_manager.hook.get_forward_models_schemas()[0].items()
        for option in set(schemas)
        if job != "select_wells"
    )
