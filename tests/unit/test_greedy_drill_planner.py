from datetime import datetime, timedelta
from itertools import product
import configsuite
from tests.unit.test_drill_planner import _advanced_setup
from spinningjenny.drill_planner import drill_planner_schema
from spinningjenny.script.drill_planner import _verify_constraints, _verify_priority
from spinningjenny.drill_planner.greedy_drill_planner import (
    _filter_events,
    _next_best_event,
    get_greedy_drill_plan,
    create_config_dictionary,
    _combine_slot_rig_unavailability,
    event_tuple,
)


def test__filter_events():
    config_suite = configsuite.ConfigSuite(
        _advanced_setup(),
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )

    config = create_config_dictionary(config_suite.snapshot)
    all_events = [
        event_tuple(well=w, slot=s, rig=r)
        for w, s, r in product(config["wells"], config["slots"], config["rigs"])
    ]

    filtered_events = _filter_events(config, all_events)

    for event in filtered_events:
        assert event.well in config["rigs"][event.rig]["wells"]
        assert event.well in config["slots"][event.slot]["wells"]
        assert event.slot in config["rigs"][event.rig]["slots"]


def test__next_best_event():
    config_suite = configsuite.ConfigSuite(
        _advanced_setup(),
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )

    config = create_config_dictionary(config_suite.snapshot)
    all_events = [
        event_tuple(well=w, slot=s, rig=r)
        for w, s, r in product(
            sorted(config["wells"]), sorted(config["slots"]), sorted(config["rigs"])
        )
    ]

    filtered_events = _filter_events(config, all_events)
    best_event = _next_best_event(config, filtered_events)
    assert best_event == event_tuple(well="W1", slot="S1", rig="A")


def test_drill_time():
    config_suite = configsuite.ConfigSuite(
        _advanced_setup(),
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )

    config = create_config_dictionary(config_suite.snapshot)
    config["wells"]["W1"]["drill_time"] = 9999
    all_events = [
        event_tuple(well=w, slot=s, rig=r)
        for w, s, r in product(config["wells"], config["slots"], config["rigs"])
    ]

    filtered_events = _filter_events(config, all_events)

    for event in filtered_events:
        assert event.well != "W1"


def test__combine_slot_rig_unavailability():
    config_suite = configsuite.ConfigSuite(
        _advanced_setup(),
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )

    test_event = event_tuple(well="W1", slot="S1", rig="A")

    config = create_config_dictionary(config_suite.snapshot)
    config["slots"]["S1"]["unavailability"] = [
        [config["start_date"], config["end_date"]]
    ]

    expected_unavailability = [[config["start_date"], config["end_date"]]]
    unavailability = _combine_slot_rig_unavailability(config, test_event)

    assert unavailability == expected_unavailability

    config = create_config_dictionary(config_suite.snapshot)
    config["slots"]["S1"]["unavailability"] = [
        [config["start_date"], datetime(2000, 6, 1)]
    ]
    config["rigs"]["A"]["unavailability"] = [[datetime(2000, 6, 1), config["end_date"]]]
    unavailability = _combine_slot_rig_unavailability(config, test_event)

    assert unavailability == expected_unavailability

    config = create_config_dictionary(config_suite.snapshot)
    config["slots"]["S1"]["unavailability"] = [
        [datetime(2000, 3, 1), config["end_date"]]
    ]
    config["rigs"]["A"]["unavailability"] = [
        [config["start_date"], datetime(2000, 9, 1)]
    ]
    unavailability = _combine_slot_rig_unavailability(config, test_event)

    assert unavailability == expected_unavailability

    config = create_config_dictionary(config_suite.snapshot)
    config["slots"]["S1"]["unavailability"] = [
        [datetime(2000, 3, 15), datetime(2000, 6, 14)]
    ]
    config["rigs"]["A"]["unavailability"] = [
        [datetime(2000, 9, 1), datetime(2000, 11, 1)]
    ]
    unavailability = _combine_slot_rig_unavailability(config, test_event)

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

    config = configsuite.ConfigSuite(
        config,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )

    copied_config = config.snapshot
    schedule = get_greedy_drill_plan(copied_config)
    _verify_constraints(copied_config, schedule)
    _verify_priority(schedule, copied_config)
