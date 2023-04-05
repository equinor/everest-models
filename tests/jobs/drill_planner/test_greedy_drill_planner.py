import datetime
from copy import deepcopy

import pytest

from spinningjenny.jobs.fm_drill_planner.data import DayRange, Rig, Slot, WellPriority
from spinningjenny.jobs.fm_drill_planner.planner.greedy import (
    _combine_slot_rig_unavailability,
    _get_unavailability,
    _next_best_event,
    _valid_events,
    get_greedy_drill_plan,
)

START_DATE, END_DATE = datetime.date(2000, 1, 1), datetime.date(2001, 1, 1)


def get_slot(value):
    return Slot(
        value["wells"],
        [DayRange(begin, end) for begin, end in value["day_ranges"]],
    )


def get_rig(value):
    return Rig(
        value["wells"],
        value["slots"],
        [DayRange(begin, end) for begin, end in value["day_ranges"]],
        value["delay"],
    )


def get_input_values(values):
    return (
        {key: WellPriority(**value) for key, value in values["wells"].items()},
        {key: get_slot(value) for key, value in values["slots"].items()},
        {key: get_rig(value) for key, value in values["rigs"].items()},
        int(values["horizon"]),
    )


def test__next_best_event(advanced_config):
    config = deepcopy(advanced_config)
    slots_for_wells = [
        [slot for slot in config["slots"] if well in config["slots"][slot]["wells"]]
        for well in config["wells"]
    ]
    wells, slots, rigs, horizon = get_input_values(config)
    best_event = _next_best_event(
        _valid_events(wells, slots, rigs, horizon),
        wells,
        slots_for_wells,
    )

    assert best_event.well == "W1"
    assert best_event.slot == "S1"
    assert best_event.rig == "A"
    assert best_event.begin == 0
    assert best_event.end == 10


def test_drill_time(advanced_config):
    config = deepcopy(advanced_config)

    config["wells"]["W1"]["drill_time"] = 9999

    assert "W1" not in [
        event.well for event in _valid_events(*get_input_values(config))
    ]


@pytest.mark.parametrize(
    "day_ranges, expected",
    (
        pytest.param(
            {"S1": [(0, 366)], "A": []},
            [(0, 366)],
            id="slot start to end and rig no day_range",
        ),
        pytest.param(
            {
                "S1": [(0, (datetime.date(2000, 6, 1) - START_DATE).days)],
                "A": [((datetime.date(2000, 6, 1) - START_DATE).days, 366)],
            },
            [(0, 366)],
            id="slot from start and rig to end",
        ),
        pytest.param(
            {
                "S1": [((datetime.date(2000, 3, 1) - START_DATE).days, 366)],
                "A": [(0, (datetime.date(2000, 9, 1) - START_DATE).days)],
            },
            [(0, 366)],
            id="slot to end and rig from start",
        ),
        pytest.param(
            {
                "S1": [
                    (
                        (datetime.date(2000, 3, 15) - START_DATE).days,
                        (datetime.date(2000, 6, 14) - START_DATE).days,
                    )
                ],
                "A": [
                    (
                        (datetime.date(2000, 9, 1) - START_DATE).days,
                        (datetime.date(2000, 11, 1) - START_DATE).days,
                    )
                ],
            },
            [
                (
                    (datetime.date(2000, 3, 15) - START_DATE).days,
                    (datetime.date(2000, 6, 14) - START_DATE).days,
                ),
                (
                    (datetime.date(2000, 9, 1) - START_DATE).days,
                    (datetime.date(2000, 11, 1) - START_DATE).days,
                ),
            ],
            id="slot and rig between start and end",
        ),
    ),
)
def test__combine_slot_rig_unavailability(day_ranges, expected, advanced_config):
    config = deepcopy(advanced_config)

    slot, rig = "S1", "A"
    config["slots"][slot]["day_ranges"] = day_ranges[slot]
    config["rigs"][rig]["day_ranges"] = day_ranges[rig]

    assert (
        list(
            _combine_slot_rig_unavailability(
                _get_unavailability(
                    config["horizon"],
                    get_slot(config["slots"][slot]),
                    get_rig(config["rigs"][rig]),
                )
            )
        )
        == expected
    )


def test_drill_delay(small_config_include_day_ranges):
    config = deepcopy(small_config_include_day_ranges)

    # days after a drilling event the rig is unavailable
    delay_dict = {"A": 5, "B": 4}
    for name, rig in config["rigs"].items():
        rig["delay"] = delay_dict[name]
    wells, slots, rigs, horizon = get_input_values(config)
    schedule = get_greedy_drill_plan(wells, slots, rigs, horizon)
    assert schedule[0].begin == delay_dict[schedule[0].rig]
    assert (
        schedule[1].begin
        == next(
            _combine_slot_rig_unavailability(
                _get_unavailability(
                    horizon,
                    slots[schedule[1].slot],
                    rigs[schedule[1].rig],
                )
            )
        )[1]
        + delay_dict[schedule[1].rig]
        + 1
    )


def test_uncompleted_task(small_config_include_day_ranges):
    """
    Tests that the greedy drill planner doesn't error out
    when it checks an undrillable well
    """
    config = deepcopy(small_config_include_day_ranges)

    # Add extra well (but no extra slot)
    well = "W3"
    config["rigs"]["A"]["wells"].append(well)
    config["slots"]["S2"]["wells"].append(well)
    config["wells"].update({well: {"drill_time": 50, "priority": 6}})

    wells, slots, rigs, horizon = get_input_values(config)
    schedule = get_greedy_drill_plan(wells, slots=slots, rigs=rigs, horizon=horizon)

    # W2 is not drilled, there are 3 wells with 2 slots and W3 has the lowest priority
    assert "W2" not in [task.well for task in schedule]
