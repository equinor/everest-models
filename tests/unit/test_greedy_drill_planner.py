from copy import deepcopy
from datetime import datetime

from spinningjenny.drill_planner import (
    combine_slot_rig_unavailability,
    create_config_dictionary,
    date_to_int,
)
from spinningjenny.drill_planner.drillmodel import FieldManager, FieldSchedule
from spinningjenny.drill_planner.greedy_drill_planner import (
    _next_best_event,
    _valid_events,
    get_greedy_drill_plan,
)
from tests.unit.test_drill_planner import (
    _advanced_setup,
    _delayed_advanced_setup,
    _small_setup_incl_unavailability_config,
    get_drill_planner_config_snapshot,
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
    assert best_event.well == "W1"
    assert best_event.slot == "S1"
    assert best_event.rig == "A"
    assert best_event.begin == 0
    assert best_event.end == 10


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

    config["slots"]["S1"]["unavailability"] = [[0, config["horizon"]]]

    expected_unavailability = [[0, config["horizon"]]]
    unavailability = combine_slot_rig_unavailability(config, test_slot, test_rig)

    assert unavailability == expected_unavailability

    config = create_config_dictionary(config_snapshot)
    config["slots"]["S1"]["unavailability"] = [
        [0, date_to_int(datetime(2000, 6, 1), config_snapshot)]
    ]
    config["rigs"]["A"]["unavailability"] = [
        [date_to_int(datetime(2000, 6, 1), config_snapshot), config["horizon"]]
    ]
    unavailability = combine_slot_rig_unavailability(config, test_slot, test_rig)

    assert unavailability == expected_unavailability

    config = create_config_dictionary(config_snapshot)
    config["slots"]["S1"]["unavailability"] = [
        [date_to_int(datetime(2000, 3, 1), config_snapshot), config["horizon"]]
    ]
    config["rigs"]["A"]["unavailability"] = [
        [0, date_to_int(datetime(2000, 9, 1), config_snapshot)]
    ]
    unavailability = combine_slot_rig_unavailability(config, test_slot, test_rig)

    assert unavailability == expected_unavailability

    config = create_config_dictionary(config_snapshot)
    config["slots"]["S1"]["unavailability"] = [
        [
            date_to_int(datetime(2000, 3, 15), config_snapshot),
            date_to_int(datetime(2000, 6, 14), config_snapshot),
        ]
    ]
    config["rigs"]["A"]["unavailability"] = [
        [
            date_to_int(datetime(2000, 9, 1), config_snapshot),
            date_to_int(datetime(2000, 11, 1), config_snapshot),
        ]
    ]
    unavailability = combine_slot_rig_unavailability(config, test_slot, test_rig)

    expected_unavailability = [
        [
            date_to_int(datetime(2000, 3, 15), config_snapshot),
            date_to_int(datetime(2000, 6, 14), config_snapshot),
        ],
        [
            date_to_int(datetime(2000, 9, 1), config_snapshot),
            date_to_int(datetime(2000, 11, 1), config_snapshot),
        ],
    ]
    assert unavailability == expected_unavailability


def test_greedy_drill_plan():
    """
    Tests that the greedy drill planner gives a feasible schedule
    """
    config = _delayed_advanced_setup()

    config_snapshot = get_drill_planner_config_snapshot(config)
    config_dic = create_config_dictionary(config_snapshot)
    schedule = get_greedy_drill_plan(deepcopy(config_dic), [])

    field_manager = FieldManager.generate_from_snapshot(config_snapshot)
    field_schedule = FieldSchedule(schedule)

    assert field_manager.valid_schedule(field_schedule)


def test_drill_delay():
    config = _small_setup_incl_unavailability_config()

    # days after a drilling event the rig is unavailable
    delay_dict = {"A": 5, "B": 4}
    for rig in config["rigs"]:
        rig["delay"] = delay_dict[rig["name"]]

    config_snapshot = get_drill_planner_config_snapshot(config)
    config_dic = create_config_dictionary(config_snapshot)
    schedule = get_greedy_drill_plan(deepcopy(config_dic), [])
    assert schedule[0].begin == delay_dict[schedule[0].rig]
    assert (
        schedule[1].begin
        == combine_slot_rig_unavailability(
            config_dic, schedule[1].slot, schedule[1].rig
        )[0][1]
        + delay_dict[schedule[1].rig]
        + 1
    )

    field_manager = FieldManager.generate_from_snapshot(config_snapshot)
    field_schedule = FieldSchedule(schedule)

    assert field_manager.valid_schedule(field_schedule)


def test_uncompleted_task():
    """
    Tests that the greedy drill planner doesn't error out
    when it checks an undrillable well
    """
    config = _small_setup_incl_unavailability_config()

    # Add extra well (but no extra slot)
    config["rigs"][0]["wells"].append("W3")
    config["slots"][1]["wells"].append("W3")
    config["wells"].append({"name": "W3", "drill_time": 50})
    config["wells_priority"]["W3"] = 6

    config_snapshot = get_drill_planner_config_snapshot(config)
    config_dic = create_config_dictionary(config_snapshot)
    schedule = get_greedy_drill_plan(deepcopy(config_dic), [])

    drilled_wells = [task.well for task in schedule]

    # W2 is not drilled, there are 3 wells with 2 slots and W3 has the lowest priority
    assert "W2" not in drilled_wells
