import collections
from copy import deepcopy

import pytest
from configsuite import ConfigSuite
from sub_testdata import DRILL_PLANNER as TEST_DATA

from spinningjenny.jobs.fm_drill_planner import drill_planner_schema
from spinningjenny.jobs.fm_drill_planner.cli import _compare_schedules, _prepare_config
from spinningjenny.jobs.fm_drill_planner.drillmodel import FieldManager
from spinningjenny.jobs.fm_drill_planner.greedy_drill_planner import (
    get_greedy_drill_plan,
)
from spinningjenny.jobs.fm_drill_planner.ormodel import (
    drill_constraint_model,
    run_optimization,
)
from spinningjenny.jobs.fm_drill_planner.utils import (
    Event,
    add_missing_slots,
    resolve_priorities,
)
from spinningjenny.jobs.shared.io_utils import load_yaml


def get_drill_planner_configsuite(config_dic):
    config_dic = add_missing_slots(config_dic)
    config_suite = ConfigSuite(
        config_dic,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
        deduce_required=True,
    )
    assert config_suite.valid
    return config_suite


def get_drill_planner_config_snapshot(config_dic):
    return get_drill_planner_configsuite(config_dic).snapshot


# def _build_config(raw_config):
#     raw_config = add_missing_slots(raw_config)
#     return ConfigSuite(
#         raw_config,
#         drill_planner_schema.build(),
#         extract_validation_context=drill_planner_schema.extract_validation_context,
#         deduce_required=True,
#     )


# @pytest.mark.parametrize(
#     "remove_slots_from_rigs, remove_slots",
#     [(False, False), (True, False), (True, True)],
# )
# def test_simple_well_order(remove_slots_from_rigs, remove_slots):
#     # Slots can be removed from the rigs, the slots entry is then optional.
#     config = _simple_setup_config(
#         remove_slots_from_rigs=remove_slots_from_rigs, remove_slots=remove_slots
#     )
#     well_order = [("W1", 0, 5), ("W2", 6, 16)]

#     field_manager = FieldManager.generate_from_config(**config)
#     schedule = run_optimization(field_manager=field_manager)

#     assert field_manager.valid_schedule(schedule)

#     schedule_well_order = [(elem.well, elem.begin, elem.end) for elem in schedule]

#     assert len(schedule) == len(well_order)
#     assert all(test_task in schedule_well_order for test_task in well_order)
#     assert all(schedule_task in well_order for schedule_task in schedule_well_order)


def test_rig_slot_reservation(advanced_drill_constraints_model):
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

    schedule = run_optimization(drill_constraint_model=advanced_drill_constraints_model)

    # assert field_manager.valid_schedule(schedule)

    schedule_well_order = [(elem.well, elem.begin, elem.end) for elem in schedule]
    assert len(schedule) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)


def test_rig_slot_include_delay(delayed_drill_constraints_model):
    """
    W1 is drilled first and must be drilled in rig A or B -> rig A unavailable
    thus W1 at B. W1 can be drilled in slot 3 and 5, but slot 3 must be used
    for W5. Thus W1, S5, B.

    W2 can be drilled in rig A and B. There's not enough time left in rig B to
    drill W2, before it becomes unavailable, rig A becomes avaiable again
    before rig B, thus W2 must be drilled at rig A. Rig A is unavailable till
    2.5, hence drilling starts after that. W2 can be drill in any of S2, S4 and
    S1.

    W3 can be drilled at all rigs. Rig A is occupied drilling W2 until 3.6.
    There is not enough time to drill W3 in rig B before it becomes unavailable
    after drilling W1. None of the remaining slots have enough time to drill W3
    before Rig C is unavailable. Thus W3 must be drilled at the first available
    rig, which is rig B.

    W4 has a shorter drill time than W3 (by 5 days), and the timeslot at Rig B
    is large enough to drill W4. Drilling W4 before W3 has no effect on when W3
    is drilled, it wouldn't be able to drill in that timeslot, so W4 is drilled
    in advance of W3 despite lower priority.

    The final well, W5, must be drilled at Rig C, which is available 2.24,
    after a rig unavailable period.
    """

    detailed_well_order = [
        ("B", "W1", "S5", 0, 10),
        ("A", "W2", "S2", 36, 66),
        ("B", "W3", "S4", 44, 69),
        ("C", "W4", "S1", 11, 31),
        ("C", "W5", "S3", 55, 95),
    ]

    well_order = [
        (well, begin, end) for (_, well, _, begin, end) in detailed_well_order
    ]

    # field_manager = FieldManager.generate_from_config(**delayed_advanced_setup())
    schedule = run_optimization(drill_constraint_model=delayed_drill_constraints_model)

    # assert field_manager.valid_schedule(schedule)

    schedule_well_order = [(elem.well, elem.begin, elem.end) for elem in schedule]
    assert len(schedule) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)


# @pytest.mark.slow
# @pytest.mark.parametrize(
#     "remove_slots_from_rigs, remove_slots",
#     [(False, False), (True, False), (True, True)],
# )
# def test_default_large_setup(remove_slots_from_rigs, remove_slots):
#     """
#     Test that a larger setup without restrictions works

#     We only verify that it is possible to set it up using or-tools, not that
#     the solution itself is optimal.
#     """
#     # Slots can be removed from the rigs, the slots entry is then optional.
#     config = _large_setup(
#         remove_slots_from_rigs=remove_slots_from_rigs, remove_slots=remove_slots
#     )
#     field_manager = FieldManager.generate_from_config(**config)
#     schedule = run_optimization(
#         field_manager=field_manager, solution_limit=1, accepted_status=cp_model.FEASIBLE
#     )

#     assert field_manager.valid_schedule(schedule)


# @pytest.mark.slow
# def test_many_wells_one_rig(large_setup):
#     """
#     A setup without restrictions and single rig can be solved easily by the
#     greedy planner, while the sat solver could have more difficulties. Some
#     work has been done to facilitate the or tools to understand the simple
#     solution. We verify that single rig, 40 wells is possible to solve in a
#     short amount of time. The quick solving is only applicable in scenarios
#     where no well can be drilled by more than a single rig.

#     40 wells seems to take about 5 seconds and 70 wells takes about 50 seconds.
#     The time taken seems evenly split among the greedy planner and the or-tools
#     planner.

#     """
#     config = deepcopy(large_setup)
#     # Reduce problem to single rig
#     del config["rigs"]["B"]
#     del config["rigs"]["C"]

#     field_manager = FieldManager.generate_from_config(**config)

#     greedy_schedule = get_greedy_drill_plan([], **config)
#     assert field_manager.valid_schedule(greedy_schedule)

#     schedule = run_optimization(
#         drill_constraint_model(
#             field_manager.well_dict,
#             field_manager.slot_dict,
#             field_manager.rig_dict,
#             field_manager.horizon,
#             best_guess_schedule=greedy_schedule,
#         )
#     )
#     assert field_manager.valid_schedule(schedule)


# def test_invalid_config_schema():
#     raw_config = _small_setup_incl_unavailability_config()
#     raw_config["rigs"]["A"]["unavailability"].append(
#         (-10,10)
#     )
#     config_suite = _build_config(raw_config)

#     assert not config_suite.valid

#     raw_config = _small_setup_incl_unavailability_config()
#     raw_config["rigs"]["A"]["slots"].append("UNKNOWN_SLOT")
#     config_suite = _build_config(raw_config)

#     assert not config_suite.valid

#     raw_config = _small_setup_incl_unavailability_config()
#     raw_config["wells_priority"]["UNKNOWN_WELL"] = 10
#     config_suite = _build_config(raw_config)

#     assert not config_suite.valid

#     raw_config = _small_setup_incl_unavailability_config()
#     raw_config["slots"]["S2"]["unavailability"].append(
#         (-10,10)
#     )
#     config_suite = _build_config(raw_config)

#     assert not config_suite.valid

#     raw_config = _small_setup_incl_unavailability_config()
#     raw_config["slots"][1]["unavailability"].append(
#         (10,365+11)  # a year and 11 days
#     )
#     config_suite = _build_config(raw_config)

#     assert not config_suite.valid

#     # The rigs have slots, but the slots entry is missing.
#     raw_config = _simple_setup_config(remove_slots_from_rigs=False, remove_slots=True)
#     config_suite = _build_config(raw_config)

#     assert not config_suite.valid


def test_script_prepare_config(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    config = _prepare_config(
        config=load_yaml("config.yml"),
        optimizer_values=load_yaml("optimizer_values.yml"),
        input_values=load_yaml("wells.json"),
    )
    assert config.valid


def test_script_resolve_priorities():
    # The function takes a configsuite snapshot,
    # but it is really only interested in the priorities part
    configtype = collections.namedtuple("mock_snapshot", "wells_priority")
    wells_priority = [("W1", 3), ("W2", 2), ("W3", 1)]
    config = configtype(wells_priority)

    # Only one well must be shifted (W3)
    well_order = [
        ("B", "S5", "W1", 1, 10),
        ("A", "S2", "W2", 1, 20),
        ("B", "S4", "W3", 1, 15),
    ]
    schedule_list = [
        Event(rig=x[0], slot=x[1], well=x[2], begin=x[3], end=x[4]) for x in well_order
    ]

    modified_schedule = resolve_priorities(schedule_list, config)
    assert modified_schedule[0].end == 10
    assert modified_schedule[1].end == 20
    assert modified_schedule[2].end == 20

    # Completion dates for the scheduled wells are not modified
    assert modified_schedule[0].completion == 10
    assert modified_schedule[1].completion == 20
    assert modified_schedule[2].completion == 15

    # Both W2 and W3 must be shifted
    well_order = [
        ("B", "S5", "W1", 1, 20),
        ("A", "S2", "W2", 1, 15),
        ("B", "S4", "W3", 1, 10),
    ]
    schedule_list = [
        Event(rig=x[0], slot=x[1], well=x[2], begin=x[3], end=x[4]) for x in well_order
    ]

    modified_schedule = resolve_priorities(schedule_list, config)
    assert modified_schedule[0].end == 20
    assert modified_schedule[1].end == 20
    assert modified_schedule[2].end == 20

    # Completion dates for the scheduled wells are not modified
    assert modified_schedule[0].completion == 20
    assert modified_schedule[1].completion == 15
    assert modified_schedule[2].completion == 10


def test_compare_schedules():
    wells_priority = {"W1": 1, "W2": 0.5, "W3": 0}
    well_order = [
        ("B", "S5", "W1", 1, 10),
        ("A", "S2", "W2", 1, 20),
        ("B", "S4", "W3", 1, 15),
    ]
    schedule_list = [
        Event(rig=x[0], slot=x[1], well=x[2], begin=x[3], end=x[4]) for x in well_order
    ]
    assert schedule_list == _compare_schedules(schedule_list, None, wells_priority)
    assert schedule_list == _compare_schedules(
        schedule_list, schedule_list[:-1], wells_priority
    )

    better_well_order = [
        ("B", "S5", "W1", 1, 10),
        ("A", "S2", "W2", 1, 15),
        ("B", "S4", "W3", 1, 15),
    ]
    better_schedule_list = [
        Event(rig=x[0], slot=x[1], well=x[2], begin=x[3], end=x[4])
        for x in better_well_order
    ]
    assert better_schedule_list == _compare_schedules(
        schedule_list, better_schedule_list, wells_priority
    )


def test_inclusive_bounds_no_unavailability(
    simple_setup_config, simple_drill_constraints_model
):
    config = deepcopy(simple_setup_config)
    schedule = run_optimization(simple_drill_constraints_model)

    # assert field_manager.valid_schedule(schedule)
    sorted_schedule = sorted(
        schedule,
        key=lambda element: config["wells_priority"][element.well],
        reverse=True,
    )
    assert sorted_schedule[1].begin > sorted_schedule[0].end


@pytest.mark.parametrize(
    "expected_begins, key, unavailability",
    (
        pytest.param(
            {"W1": 1}, "slots", {"S1": [(0, 0)], "S2": [(0, 0)]}, id="slot at start"
        ),
        pytest.param(
            {"W1": 6},
            "slots",
            {"S1": [(5, 5)], "S2": [(5, 5)]},
            id="slot insufficient time",
        ),
        pytest.param(
            {"W1": 0},
            "slots",
            {"S1": [(6, 6)], "S2": [(6, 6)]},
            id="slot sufficient time",
        ),
        pytest.param(
            {"W1": 12},
            "slots",
            {"S1": [(5, 5), (11, 11)], "S2": [(5, 5), (11, 11)]},
            id="slot multi events insufficient time",
        ),
        pytest.param(
            {"W1": 6},
            "slots",
            {"S1": [(5, 5), (12, 12)], "S2": [(5, 5), (12, 12)]},
            id="slots multi events sufficient time",
        ),
        pytest.param({"W1": 1}, "rigs", {"A": [(0, 0)]}, id="rig at start"),
        pytest.param({"W1": 6}, "rigs", {"A": [(5, 5)]}, id="rig insufficient time"),
        pytest.param({"W1": 0}, "rigs", {"A": [(6, 6)]}, id="rig sufficient time"),
        pytest.param(
            {"W1": 12},
            "rigs",
            {"A": [(5, 5), (11, 11)]},
            id="rigs multi events insufficient time",
        ),
        pytest.param(
            {"W1": 6},
            "rigs",
            {"A": [(5, 5), (12, 12)]},
            id="rigs multi events sufficient time",
        ),
    ),
)
def test_unavailable(expected_begins, key, unavailability, simple_setup_config):
    config = deepcopy(simple_setup_config)

    for event, ranges in unavailability.items():
        config[key][event]["unavailability"] = ranges

    field_manager = FieldManager.generate_from_config(**config)
    schedule = run_optimization(
        drill_constraint_model(
            field_manager.well_dict,
            field_manager.slot_dict,
            field_manager.rig_dict,
            field_manager.horizon,
        )
    )
    assert field_manager.valid_schedule(schedule)

    for well_name, expected_begin in expected_begins.items():
        assert [elem.begin for elem in schedule if elem.well == well_name] == [
            expected_begin
        ]
