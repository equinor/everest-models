import datetime
from copy import deepcopy

from spinningjenny.jobs.fm_drill_planner.drillmodel import FieldManager
from spinningjenny.jobs.fm_drill_planner.greedy_drill_planner import (
    _next_best_event,
    _valid_events,
    get_greedy_drill_plan,
)
from spinningjenny.jobs.fm_drill_planner.utils import (
    combine_slot_rig_unavailability,
    get_unavailability,
)


def test__filter_events(advanced_setup):
    config = deepcopy(advanced_setup)

    filtered_events = _valid_events(
        config["wells"], config["slots"], config["rigs"], config["horizon"]
    )

    for event in filtered_events:
        assert event.well in config["rigs"][event.rig]["wells"]
        assert event.well in config["slots"][event.slot]["wells"]
        assert event.slot in config["rigs"][event.rig]["slots"]


def test__next_best_event(advanced_setup):
    config = deepcopy(advanced_setup)
    slots_for_wells = [
        [slot for slot in config["slots"] if well in config["slots"][slot]["wells"]]
        for well in config["wells"]
    ]
    best_event = _next_best_event(
        _valid_events(
            config["wells"], config["slots"], config["rigs"], config["horizon"]
        ),
        config["wells"],
        slots_for_wells,
    )

    assert best_event.well == "W1"
    assert best_event.slot == "S1"
    assert best_event.rig == "A"
    assert best_event.begin == 0
    assert best_event.end == 10


def test_drill_time(advanced_setup):
    config = deepcopy(advanced_setup)

    config["wells"]["W1"]["drill_time"] = 9999
    filtered_events = _valid_events(
        config["wells"], config["slots"], config["rigs"], config["horizon"]
    )

    for event in filtered_events:
        assert event.well != "W1"


def test__combine_slot_rig_unavailability(advanced_setup):
    config = deepcopy(advanced_setup)

    test_slot = "S1"
    test_rig = "A"

    config["slots"]["S1"]["unavailability"] = [[0, config["horizon"]]]

    expected_unavailability = [(0, config["horizon"])]
    unavailability = list(
        combine_slot_rig_unavailability(
            get_unavailability(
                config["horizon"], config["slots"][test_slot], config["rigs"][test_rig]
            )
        )
    )

    assert unavailability == expected_unavailability

    config["slots"]["S1"]["unavailability"] = [
        [0, (datetime.date(2000, 6, 1) - config["start_date"]).days]
    ]
    config["rigs"]["A"]["unavailability"] = [
        [(datetime.date(2000, 6, 1) - config["start_date"]).days, config["horizon"]]
    ]
    unavailability = list(
        combine_slot_rig_unavailability(
            get_unavailability(
                config["horizon"], config["slots"][test_slot], config["rigs"][test_rig]
            )
        )
    )

    assert unavailability == expected_unavailability

    config["slots"]["S1"]["unavailability"] = [
        [(datetime.date(2000, 3, 1) - config["start_date"]).days, config["horizon"]]
    ]
    config["rigs"]["A"]["unavailability"] = [
        [0, (datetime.date(2000, 9, 1) - config["start_date"]).days]
    ]
    unavailability = list(
        combine_slot_rig_unavailability(
            get_unavailability(
                config["horizon"], config["slots"][test_slot], config["rigs"][test_rig]
            )
        )
    )

    assert unavailability == expected_unavailability

    config["slots"]["S1"]["unavailability"] = [
        [
            (datetime.date(2000, 3, 15) - config["start_date"]).days,
            (datetime.date(2000, 6, 14) - config["start_date"]).days,
        ]
    ]
    config["rigs"]["A"]["unavailability"] = [
        [
            (datetime.date(2000, 9, 1) - config["start_date"]).days,
            (datetime.date(2000, 11, 1) - config["start_date"]).days,
        ]
    ]
    unavailability = list(
        combine_slot_rig_unavailability(
            get_unavailability(
                config["horizon"], config["slots"][test_slot], config["rigs"][test_rig]
            )
        )
    )

    expected_unavailability = [
        (
            (datetime.date(2000, 3, 15) - config["start_date"]).days,
            (datetime.date(2000, 6, 14) - config["start_date"]).days,
        ),
        (
            (datetime.date(2000, 9, 1) - config["start_date"]).days,
            (datetime.date(2000, 11, 1) - config["start_date"]).days,
        ),
    ]
    assert unavailability == expected_unavailability


def test_greedy_drill_plan(delayed_advanced_setup):
    """
    Tests that the greedy drill planner gives a feasible schedule
    """
    schedule = get_greedy_drill_plan([], **deepcopy(delayed_advanced_setup))

    field_manager = FieldManager.generate_from_config(**delayed_advanced_setup)
    assert field_manager.valid_schedule(schedule)


def test_drill_delay(small_setup_incl_unavailability_config):
    config = deepcopy(small_setup_incl_unavailability_config)

    # days after a drilling event the rig is unavailable
    delay_dict = {"A": 5, "B": 4}
    for name, rig in config["rigs"].items():
        rig["delay"] = delay_dict[name]

    schedule = get_greedy_drill_plan([], **deepcopy(config))
    assert schedule[0].begin == delay_dict[schedule[0].rig]
    assert (
        schedule[1].begin
        == next(
            combine_slot_rig_unavailability(
                get_unavailability(
                    config["horizon"],
                    config["slots"][schedule[1].slot],
                    config["rigs"][schedule[1].rig],
                )
            )
        )[1]
        + delay_dict[schedule[1].rig]
        + 1
    )


def test_uncompleted_task(small_setup_incl_unavailability_config):
    """
    Tests that the greedy drill planner doesn't error out
    when it checks an undrillable well
    """
    config = deepcopy(small_setup_incl_unavailability_config)

    # Add extra well (but no extra slot)
    well = "W3"
    config["rigs"]["A"]["wells"].append(well)
    config["slots"]["S2"]["wells"].append(well)
    config["wells"].update({well: {"drill_time": 50, "priority": 6}})
    config["wells_priority"][well] = 6

    schedule = get_greedy_drill_plan([], **config)

    # W2 is not drilled, there are 3 wells with 2 slots and W3 has the lowest priority
    assert "W2" not in [task.well for task in schedule]
