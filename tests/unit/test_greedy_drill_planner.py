from datetime import datetime, timedelta
from copy import deepcopy

from tests.unit.test_drill_planner import (
    _advanced_setup,
    verify_priority,
    get_drill_planner_config_snapshot,
)

from spinningjenny.drill_planner import (
    create_config_dictionary,
    verify_constraints,
    combine_slot_rig_unavailability,
)
from spinningjenny.drill_planner.drill_planner_optimization import ScheduleEvent
from spinningjenny.drill_planner.greedy_drill_planner import (
    _valid_events,
    _next_best_event,
    get_greedy_drill_plan,
)


def test__filter_events():
    config_snapshot = get_drill_planner_config_snapshot(_advanced_setup())
    config = create_config_dictionary(config_snapshot)

    filtered_events = _valid_events(config)

    for event in filtered_events:
        assert event.well in config["rigs"][event.rig]["wells"]
        assert event.well in config["slots"][event.slot]["wells"]
        assert event.slot in config["rigs"][event.rig]["slots"]


def test__next_best_event():
    config_snapshot = get_drill_planner_config_snapshot(_advanced_setup())
    config = create_config_dictionary(config_snapshot)

    filtered_events = _valid_events(config)
    best_event = _next_best_event(config, filtered_events)

    assert best_event == ScheduleEvent(
        well="W1",
        slot="S1",
        rig="A",
        start_date=datetime(2000, 1, 1),
        end_date=datetime(2000, 1, 11),
    )


def test_drill_time():
    config_snapshot = get_drill_planner_config_snapshot(_advanced_setup())
    config = create_config_dictionary(config_snapshot)

    config["wells"]["W1"]["drill_time"] = 9999
    filtered_events = _valid_events(config)

    for event in filtered_events:
        assert event.well != "W1"


def test__combine_slot_rig_unavailability():
    config_snapshot = get_drill_planner_config_snapshot(_advanced_setup())
    config = create_config_dictionary(config_snapshot)

    test_slot = "S1"
    test_rig = "A"

    config["slots"]["S1"]["unavailability"] = [
        [config["start_date"], config["end_date"]]
    ]

    expected_unavailability = [[config["start_date"], config["end_date"]]]
    unavailability = combine_slot_rig_unavailability(config, test_slot, test_rig)

    assert unavailability == expected_unavailability

    config = create_config_dictionary(config_snapshot)
    config["slots"]["S1"]["unavailability"] = [
        [config["start_date"], datetime(2000, 6, 1)]
    ]
    config["rigs"]["A"]["unavailability"] = [[datetime(2000, 6, 1), config["end_date"]]]
    unavailability = combine_slot_rig_unavailability(config, test_slot, test_rig)

    assert unavailability == expected_unavailability

    config = create_config_dictionary(config_snapshot)
    config["slots"]["S1"]["unavailability"] = [
        [datetime(2000, 3, 1), config["end_date"]]
    ]
    config["rigs"]["A"]["unavailability"] = [
        [config["start_date"], datetime(2000, 9, 1)]
    ]
    unavailability = combine_slot_rig_unavailability(config, test_slot, test_rig)

    assert unavailability == expected_unavailability

    config = create_config_dictionary(config_snapshot)
    config["slots"]["S1"]["unavailability"] = [
        [datetime(2000, 3, 15), datetime(2000, 6, 14)]
    ]
    config["rigs"]["A"]["unavailability"] = [
        [datetime(2000, 9, 1), datetime(2000, 11, 1)]
    ]
    unavailability = combine_slot_rig_unavailability(config, test_slot, test_rig)

    expected_unavailability = [
        [datetime(2000, 3, 15), datetime(2000, 6, 14)],
        [datetime(2000, 9, 1), datetime(2000, 11, 1)],
    ]
    assert unavailability == expected_unavailability


def test_greedy_drill_plan():
    """
    Tests that the greedy drill planner gives a feasible schedule
    """
    config = _advanced_setup()
    start_date = config["start_date"]

    # days after start each rig is unavailable
    unavailable = {"A": (0, 35), "B": (25, 43), "C": (32, 54)}

    for rig in config["rigs"]:
        rig["unavailability"] = [
            {
                "start": start_date + timedelta(days=unavailable[rig["name"]][0]),
                "stop": start_date + timedelta(days=unavailable[rig["name"]][1]),
            }
        ]

    # days after start each slot is unavailable
    unavailable = {
        "S1": (0, 10),
        "S2": (7, 14),
        "S3": (34, 43),  # drilling W5 must now be delayed
        "S4": (6, 18),
        "S5": (15, 18),
    }

    for slot in config["slots"]:
        slot["unavailability"] = [
            {
                "start": start_date + timedelta(days=unavailable[slot["name"]][0]),
                "stop": start_date + timedelta(days=unavailable[slot["name"]][1]),
            }
        ]

    config_snapshot = get_drill_planner_config_snapshot(config)
    config_dic = create_config_dictionary(config_snapshot)
    schedule = get_greedy_drill_plan(deepcopy(config_dic), [])
    assert not verify_constraints(config_dic, schedule)
    verify_priority(schedule, config_snapshot)
