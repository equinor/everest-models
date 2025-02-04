from copy import deepcopy

import pytest

from everest_models.jobs.fm_drill_planner.data import (
    DayRange,
    Event,
    Rig,
    Slot,
    WellPriority,
)
from everest_models.jobs.fm_drill_planner.manager import FieldManager, get_field_manager
from everest_models.jobs.fm_drill_planner.models import DrillPlanConfig

COMMANDS = {
    "well": "parse_well_priority(*wells_and_priority)",
    "config": "parse_config(drill_plan_config, False)",
    "missing": "add_missing_slots()",
}


@pytest.fixture(scope="module")
def drill_plan_config(drill_planner_config):
    config = deepcopy(drill_planner_config)
    config.pop("slots")
    for rig in config["rigs"]:
        rig.pop("slots", None)
    return DrillPlanConfig.model_validate(config)


@pytest.mark.parametrize("lint, expected", ((False, FieldManager), (True, type(None))))
def test_drill_planner_get_field_manager_lint(
    lint, expected, drill_plan_config, wells_and_priority
):
    assert isinstance(
        get_field_manager(
            drill_plan_config,
            *wells_and_priority,
            ignore_end_date=False,
            skip_creation=lint,
        ),
        expected,
    )


def test_drill_planner_manager_greedy_schedule(drill_plan_config, wells_and_priority):
    manager = get_field_manager(
        drill_plan_config,
        *wells_and_priority,
        ignore_end_date=False,
        skip_creation=False,
    )
    assert not manager._optimize_schedule
    assert manager._greedy_schedule == [
        Event(rig="A", slot="_A_slot_0", well="w1", begin=33, end=53),
        Event(rig="A", slot="_A_slot_1", well="w2", begin=79, end=104),
        Event(rig="B", slot="_B_slot_0", well="w3", begin=46, end=89),
        Event(rig="B", slot="_B_slot_1", well="w4", begin=0, end=23),
        Event(rig="B", slot="_B_slot_2", well="w5", begin=90, end=126),
    ]
    assert manager.schedule() == [
        Event(rig="A", slot="_A_slot_0", well="w1", begin=33, end=53, completion=53),
        Event(rig="A", slot="_A_slot_1", well="w2", begin=79, end=104, completion=104),
        Event(rig="B", slot="_B_slot_0", well="w3", begin=46, end=104, completion=89),
        Event(rig="B", slot="_B_slot_1", well="w4", begin=0, end=104, completion=23),
        Event(rig="B", slot="_B_slot_2", well="w5", begin=90, end=126, completion=126),
    ]


def test_drill_planner_manager_optimized_schedule(
    drill_planner_config, wells_and_priority
):
    manager = get_field_manager(
        DrillPlanConfig.model_validate(drill_planner_config),
        *wells_and_priority,
        ignore_end_date=False,
        skip_creation=False,
    )
    assert not manager._optimize_schedule
    manager.run_schedule_optimization(3600)
    assert (
        manager._greedy_schedule
        and manager._optimize_schedule
        and manager._greedy_schedule != manager._optimize_schedule
    )
    assert manager._optimize_schedule == [
        Event(rig="A", slot="S1", well="w2", begin=79, end=104),
        Event(rig="A", slot="S2", well="w1", begin=33, end=53),
        Event(rig="B", slot="S3", well="w3", begin=46, end=89),
        Event(rig="B", slot="S4", well="w4", begin=0, end=23),
        Event(rig="B", slot="S5", well="w5", begin=90, end=126),
    ]
    assert manager.schedule() == [
        Event(rig="A", slot="S2", well="w1", begin=33, end=53, completion=53),
        Event(rig="A", slot="S1", well="w2", begin=79, end=104, completion=104),
        Event(rig="B", slot="S3", well="w3", begin=46, end=104, completion=89),
        Event(rig="B", slot="S4", well="w4", begin=0, end=104, completion=23),
        Event(rig="B", slot="S5", well="w5", begin=90, end=126, completion=126),
    ]


@pytest.mark.parametrize(
    "ignore_end_date, horizon",
    (
        pytest.param(True, 365243, id="Ignore end date: True"),
        pytest.param(False, 366, id="Ignore end date: False"),
    ),
)
def test_drill_planner_manager_builder_parse_config(
    ignore_end_date, horizon, builder, drill_plan_config
):
    assert not builder._attributes
    # implicit test: parse_well_priority returns self
    assert (
        len(builder.parse_config(drill_plan_config, ignore_end_date)._attributes) == 3
    )
    assert builder._attributes["horizon"] == horizon
    assert builder._attributes["rigs"] == {
        "A": Rig(
            wells=("w1", "w2", "w3"),
            day_ranges=[DayRange(begin=0, end=32), DayRange(begin=73, end=78)],
        ),
        "B": Rig(
            wells=("w3", "w4", "w5"),
            day_ranges=[DayRange(begin=31, end=32), DayRange(begin=44, end=45)],
        ),
    }
    assert builder._attributes["slots"] == {}
    builder._reset()


def test_drill_planner_manager_builder_parse_well_priority(
    builder, small_wells_and_priority
):
    assert not builder._attributes
    # implicit test: parse_well_priority returns self
    assert len(builder.parse_well_priority(*small_wells_and_priority)._attributes) == 1
    assert builder._attributes["wells"] == {
        "W1": WellPriority(drill_time=5, priority=1),
        "W2": WellPriority(drill_time=10, priority=0.5),
    }
    builder._reset()


def test_drill_planner_manager_builder_add_missing_slots(builder, drill_plan_config):
    builder.parse_config(drill_plan_config, ignore_end_date=False)
    assert not builder._attributes["slots"]
    # implicit test: parse_well_priority returns self
    assert builder.add_missing_slots()._attributes
    assert builder._attributes["rigs"]["A"].slots == [
        "_A_slot_0",
        "_A_slot_1",
        "_A_slot_2",
    ]
    assert builder._attributes["rigs"]["B"].slots == [
        "_B_slot_0",
        "_B_slot_1",
        "_B_slot_2",
    ]
    assert builder._attributes["slots"] == {
        "_A_slot_0": Slot(wells=("w1",)),
        "_A_slot_1": Slot(wells=("w2",)),
        "_A_slot_2": Slot(wells=("w3",)),
        "_B_slot_0": Slot(wells=("w3",)),
        "_B_slot_1": Slot(wells=("w4",)),
        "_B_slot_2": Slot(wells=("w5",)),
    }
    builder._reset()


@pytest.mark.parametrize("missing", ("wells", "slots, horizon, rigs"))
def test_drill_planner_manager_builder_build_missing_wells(
    missing, builder, drill_plan_config, small_wells_and_priority
):
    _ = (
        builder.parse_config(drill_plan_config, ignore_end_date=False)
        if "wells" in missing
        else builder.parse_well_priority(*small_wells_and_priority)
    )
    with pytest.raises(
        AttributeError, match=r"Missing FieldManager Attribute\(s\):\s+"
    ) as e:
        builder.build(lint=False)
    error_str = str(e)
    assert all(missed.strip() in error_str for missed in missing.split(","))
    builder._reset()


def test_drill_planner_manager_builder_build_missing_slot_combo(
    builder, drill_plan_config, small_wells_and_priority
):
    builder.parse_config(drill_plan_config, ignore_end_date=False).parse_well_priority(
        *small_wells_and_priority
    )
    with pytest.raises(
        ValueError, match=r"No slot combination available for:\s+W1, W2"
    ):
        builder.build(lint=False)
    builder._reset()


@pytest.mark.parametrize(
    "order",
    (
        pytest.param(("well", "config", "missing"), id="well conf miss"),
        pytest.param(("config", "well", "missing"), id="conf well miss"),
        pytest.param(("config", "missing", "well"), id="conf miss well"),
    ),
)
def test_drill_planner_manager_builder_build(
    order, builder, drill_plan_config, wells_and_priority
):
    snippet = ".".join(COMMANDS[command] for command in order)
    assert isinstance(
        eval(f"builder.{snippet}.build(lint=False).manager"), FieldManager
    )


@pytest.mark.parametrize(
    "order",
    (
        pytest.param(("missing", "config", "well"), id="miss conf well"),
        pytest.param(("missing", "well", "config"), id="miss well conf"),
        pytest.param(("well", "missing", "config"), id="well miss conf"),
    ),
)
def test_drill_planner_manager_builder_build_missing_config_attributes(
    order, builder, drill_plan_config, wells_and_priority
):
    snippet = ".".join(COMMANDS[command] for command in order)
    with pytest.raises(
        AttributeError, match=r"Missing FieldManager Attribute\(s\):\s+"
    ) as e:
        eval(f"builder.{snippet}")
    error_str = str(e)
    assert all(value in error_str for value in ("rigs", "slots"))
    builder._reset()


@pytest.mark.parametrize(
    "input, expected",
    (
        pytest.param(
            {"W1": 10, "W2": 20, "W3": 15},
            ((10, 10), (20, 20), (20, 15)),
            id="Only well W3 must shift",
        ),
        pytest.param(
            {"W1": 20, "W2": 15, "W3": 10},
            ((20, 20), (20, 15), (20, 10)),
            id="Both W2 and W3 must shift",
        ),
    ),
)
def test_drill_planner_manager_resolve_priorities(input, expected):
    schedule = FieldManager(
        slots={},
        rigs={},
        horizon=0,
        wells={
            "W1": WellPriority(priority=3, drill_time=0),
            "W2": WellPriority(priority=2, drill_time=0),
            "W3": WellPriority(priority=1, drill_time=0),
        },
    )._resolve_schedule_priorities(
        schedule=[
            Event("B", "S5", "W1", 1, input["W1"]),
            Event("A", "S2", "W2", 1, input["W2"]),
            Event("B", "S4", "W3", 1, input["W3"]),
        ]
    )
    assert (
        event.end == end and event.completion == completion
        for event, (end, completion) in zip(schedule, expected)
    )


def _get_attributes(wells, rigs, horizon, slots=None, **_):
    def set_day_ranges(**kwargs):
        kwargs["day_ranges"] = [DayRange(*r) for r in kwargs.get("day_ranges", [])]
        return kwargs

    if slots is None:
        slots = {}
    return {
        "wells": {name: WellPriority(**kwargs) for name, kwargs in wells.items()},
        "slots": {
            name: Slot(**set_day_ranges(**kwargs)) for name, kwargs in slots.items()
        },
        "rigs": {
            name: Rig(**set_day_ranges(**kwargs)) for name, kwargs in rigs.items()
        },
        "horizon": horizon,
    }


def test_drill_planner_manager_rig_slot_include_delay(advanced_config):
    """
    W1 is drilled first and must be drilled in rig A or B -> rig A unavailable
    thus W1 at B. W1 can be drilled in slot 3 and 5, but slot 3 must be used
    for W5. Thus W1, S5, B.

    W2 can be drilled in rig A and B. There's not enough time left in rig B to
    drill W2, before it becomes unavailable, rig A becomes available again
    before rig B, thus W2 must be drilled at rig A. Rig A is unavailable till
    2.5, hence drilling starts after that. W2 can be drill in any of S2, S4 and
    S1.

    W3 can be drilled at all rigs. Rig A is occupied drilling W2 until 3.6.
    There is not enough time to drill W3 in rig B before it becomes unavailable
    after drilling W1. None of the remaining slots have enough time to drill W3
    before Rig C is unavailable. Thus W3 must be drilled at the first available
    rig, which is rig B.

    W4 has a shorter drill time than W3 (by 5 days), and the time slot at Rig B
    is large enough to drill W4. Drilling W4 before W3 has no effect on when W3
    is drilled, it wouldn't be able to drill in that time slot, so W4 is drilled
    in advance of W3 despite lower priority.

    The final well, W5, must be drilled at Rig C, which is available 2.24,
    after a rig unavailable period.
    """
    config = deepcopy(advanced_config)
    # days after start each rig is unavailable
    rigs = config["rigs"]
    rigs["A"]["day_ranges"] = ((0, 35),)
    rigs["B"]["day_ranges"] = ((25, 43),)
    rigs["C"]["day_ranges"] = ((32, 54),)

    # days after start each slot is unavailable
    # drilling W5 must now be delayed))
    for index, value in enumerate(
        (
            ((0, 10),),
            ((7, 14),),
            ((34, 43),),
            ((6, 18),),
            ((15, 18),),
        )
    ):
        config["slots"][f"S{index + 1}"]["day_ranges"] = value

    well_order = [
        ("W1", 0, 10),
        ("W2", 36, 66),
        ("W3", 44, 69),
        ("W4", 11, 31),
        ("W5", 55, 95),
    ]

    manager = FieldManager(**_get_attributes(**config))
    manager.run_schedule_optimization(3600)
    schedule_well_order = [
        (elem.well, elem.begin, elem.end) for elem in manager._optimize_schedule
    ]
    assert len(schedule_well_order) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)


def test_drill_planner_manager_rig_slot_reservation(advanced_config):
    """
    In order for all wells to be drilled, the wells can't be taken randomly
    from an instruction set of all possible combinations.
     - Slot 3 must be reserved to well 5
     - W4 can not be drilled at rig A, hence the first well to finish (W1)
       should not be drilled at Rig A
     - W5 can only be drilled at Rig C, Slot 3. Thus the second well to
       finish (W3) should be drilled at Rig C
    The key aspect here is that it is possible to drill the wells continuously
    given that they are assigned to specific slots and rigs

    A valid setup that will allow for this drilling regime is:
    (well='W1', rig='B', slot='S2')
    (well='W3', rig='C', slot='S1')
    (well='W2', rig='A', slot='S4')
    (well='W4', rig='B', slot='S5')
    (well='W5', rig='C', slot='S3')
    """

    well_order = [
        ("W1", 0, 10),
        ("W2", 0, 30),
        ("W3", 0, 25),
        ("W4", 11, 31),
        ("W5", 26, 66),
    ]

    manager = FieldManager(**_get_attributes(**advanced_config))
    manager.run_schedule_optimization(3600)
    schedule_well_order = [
        (elem.well, elem.begin, elem.end) for elem in manager._optimize_schedule
    ]
    assert len(schedule_well_order) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)


# @pytest.mark.slow
# @pytest.mark.parametrize(
#     "remove_rig_slots, remove_slots, single_rig",
#     (
#         pytest.param(False, False, False, id="no setup modification"),
#         pytest.param(True, False, False, id="remove rigs' slots"),
#         pytest.param(True, True, False, id="remove all slots"),
#         pytest.param(True, True, True, id="remove all slots, single rig"),
#         pytest.param(False, True, True, id="remove rigs` slots, single rig"),
#     ),
# )
# def test_drill_planner_large_config(
#     remove_rig_slots, remove_slots, single_rig, large_config, monkeypatch
# ):
#     """
#     Test that a larger setup without restrictions works

#     We only verify that it is possible to set it up using or-tools, not that
#     the solution itself is optimal.
#     """
#     config = deepcopy(large_config)
#     if single_rig:
#         del config["rigs"]["B"]
#         del config["rigs"]["C"]
#     if remove_slots:
#         del config["slots"]
#     if remove_rig_slots:
#         for rig in config["rigs"].values():
#             del rig["slots"]
#     # Slots can be removed from the rigs, the slots entry is then optional.
#     builder = FieldManagerBuilder()
#     monkeypatch.setattr(
#         builder,
#         "_attributes",
#         _get_attributes(**config),
#     )
#     manager = builder.add_missing_slots().build().manager
#     manager.run_schedule_optimization(3600)
#     assert manager.schedule()
