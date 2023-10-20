import datetime
from copy import deepcopy

import pytest
from pydantic import ValidationError

from everest_models.jobs.fm_drill_planner.models import DrillPlanConfig
from everest_models.jobs.fm_drill_planner.models.config import _Unavailability


def test_drill_planner_config_mismatch_slots(drill_planner_config):
    config_dict = deepcopy(drill_planner_config)
    config_dict["rigs"][-1]["slots"].extend(("miss", "ing"))
    with pytest.raises(
        ValidationError,
        match=r"There are rig\(s\) with mismatch slot\(s\):\s+",
    ) as e:
        DrillPlanConfig.parse_obj(config_dict)
    error_str = str(e)
    assert all(value in error_str for value in ("miss", "ing"))


def test_drill_planner_config_set_unavailability(drill_planner_config):
    config = DrillPlanConfig.parse_obj(deepcopy(drill_planner_config))
    assert _Unavailability.start_date == config.start_date
    assert _Unavailability.end_date == config.end_date


def test_drill_planner_config_default_end_date(drill_planner_config):
    config_dict = deepcopy(drill_planner_config)
    config_dict.pop("end_date")
    DrillPlanConfig.parse_obj(config_dict)
    assert _Unavailability.end_date == datetime.date(3000, 1, 1)


@pytest.mark.parametrize(
    "field, error",
    (
        pytest.param("start_date", TypeError, id="start_date"),
        pytest.param("rigs", ValidationError, id="rigs"),
    ),
)
def test_drill_planner_config_missing_field(field, error, drill_planner_config):
    config_dict = deepcopy(drill_planner_config)
    config_dict.pop(field)
    with pytest.raises(error, match=field):
        DrillPlanConfig.parse_obj(config_dict)


@pytest.mark.parametrize(
    "field, default",
    (
        pytest.param("end_date", datetime.date(3000, 1, 1), id="end_date"),
        pytest.param("slots", tuple(), id="slots"),
    ),
)
def test_drill_planner_config_defaults(field, default, drill_planner_config):
    config_dict = deepcopy(drill_planner_config)
    config_dict.pop(field)
    if field == "slots":
        for rig in config_dict["rigs"]:
            rig.pop(field)
    plan = DrillPlanConfig.parse_obj(config_dict)
    assert getattr(plan, field) == default
    if field == "slots":
        assert all(rig.slots == default for rig in plan.rigs)
