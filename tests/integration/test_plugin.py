import itertools
import sys

FORWARD_MODEL_DIR = "forward_models"


def test_hooks_registered(plugin_manager):
    assert sys.modules["spinningjenny.everest_hooks"] in plugin_manager.get_plugins()


def test_everest_hooks(plugin_manager):
    jobs = {
        "stea": f"{FORWARD_MODEL_DIR}/stea",
        "drill_planner": f"{FORWARD_MODEL_DIR}/drill_planner",
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
    }
    assert all(
        jobs[job["name"]] in job["path"]
        for job in itertools.chain.from_iterable(
            plugin_manager.hook.get_forward_models()
        )
    )
