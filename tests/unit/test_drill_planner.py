import pytest

from datetime import datetime, timedelta
from configsuite import ConfigSuite

from spinningjenny import load_yaml
from spinningjenny.drill_planner import (
    drill_planner_schema,
    create_config_dictionary,
    verify_constraints,
)
from spinningjenny.drill_planner.drill_planner_optimization import (
    evaluate,
    ScheduleEvent,
)
from spinningjenny.script.fm_drill_planner import _validate_config, main_entry_point

from tests import tmpdir, relpath

TEST_DATA_PATH = relpath("tests", "testdata", "drill_planner")


def get_drill_planner_configsuite(config_dic):
    config_suite = ConfigSuite(
        config_dic,
        drill_planner_schema.config_schema(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )
    assert config_suite.valid
    return config_suite


def get_drill_planner_config_snapshot(config_dic):
    return get_drill_planner_configsuite(config_dic).snapshot


def _simple_setup():
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2001, 1, 1)
    wells = ["W1", "W2"]
    rigs = ["A"]
    slots = ["S1", "S2"]
    config = {
        "start_date": start_date,
        "end_date": end_date,
        "wells": [{"name": "W1", "drill_time": 5}, {"name": "W2", "drill_time": 10}],
        "rigs": [{"name": rig, "wells": wells, "slots": slots} for rig in rigs],
        "slots": [{"name": slot, "wells": wells} for slot in slots],
        "wells_priority": {"W1": 1, "W2": 0.5},
    }
    config_suite = get_drill_planner_configsuite(config)

    return config_suite


def _simple_config_setup():
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2001, 1, 1)
    wells = ["W1", "W2"]
    slots = ["S1", "S2"]
    config = {
        "start_date": start_date,
        "end_date": end_date,
        "rigs": [
            {
                "name": "A",
                "wells": wells,
                "slots": slots,
                "unavailability": [
                    {"start": datetime(2000, 1, 3), "stop": datetime(2000, 1, 5)}
                ],
            },
            {
                "name": "B",
                "wells": wells,
                "slots": slots,
                "unavailability": [
                    {"start": datetime(2000, 2, 4), "stop": datetime(2000, 2, 7)}
                ],
            },
        ],
        "slots": [
            {"name": "S1", "wells": wells},
            {
                "name": "S2",
                "wells": wells,
                "unavailability": [
                    {"start": datetime(2000, 2, 4), "stop": datetime(2000, 2, 7)}
                ],
            },
        ],
        "wells": [{"name": "W1", "drill_time": 5}, {"name": "W2", "drill_time": 10}],
        "wells_priority": {"W1": 1, "W2": 0.5},
    }
    return config


def _advanced_setup():
    """
    Five wells should be drilled, there are three available rigs and a total of five slots

    The rigs can drill tree wells each: Rig A can drill the first 3 wells,
    Rig B wells 1-4 and rig C wells 3-5. (i.e. all rigs can drill well 3).

    Slot 3 is the only slot that can drill well 5. Slot 3 is also the only slot that can
    be drilled at all rigs. The logic must here handle that slot 3 is "reserved" for the
    last well.

    To reduce the overall drill time, the logic must also handle rig reservation to specific
    wells
    """
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2001, 1, 1)
    wells = ["W1", "W2", "W3", "W4", "W5"]
    slots = ["S1", "S2", "S3", "S4", "S5"]
    config = {
        "start_date": start_date,
        "end_date": end_date,
        "wells": [
            {"name": "W1", "drill_time": 10},
            {"name": "W2", "drill_time": 30},
            {"name": "W3", "drill_time": 25},
            {"name": "W4", "drill_time": 20},
            {"name": "W5", "drill_time": 40},
        ],
        "rigs": [
            {"name": "A", "wells": wells[:3], "slots": slots},
            {"name": "B", "wells": wells[:4], "slots": slots},
            {"name": "C", "wells": wells[2:], "slots": slots},
        ],
        "slots": [
            {"name": "S1", "wells": wells[:4]},
            {"name": "S2", "wells": wells[:4]},
            {"name": "S3", "wells": wells},
            {"name": "S4", "wells": wells[:4]},
            {"name": "S5", "wells": wells[:4]},
        ],
        "wells_priority": {"W1": 5, "W2": 4, "W3": 3, "W4": 2, "W5": 1},
    }

    return config


def _large_setup():
    """
    We're starting out fairly small - this should grow to at least 50 wells, perhaps 100

    14 wells should be drilled, there are three available rigs and a total of 14 slots
    """
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2020, 1, 1)
    wells = ["W" + str(i) for i in range(1, 15)]
    slots = ["S" + str(i) for i in range(1, 15)]
    rigs = ["A", "B", "C"]
    drill_times = [30, 20, 40, 25, 35, 75, 33, 90, 23, 32, 10, 42, 38, 47, 53]
    wells_priority = zip(wells, range(len(wells), 0, -1))
    config = {
        "start_date": start_date,
        "end_date": end_date,
        "wells": [
            {"name": w, "drill_time": drill_times[i]} for i, w in enumerate(wells)
        ],
        "rigs": [{"name": rig, "wells": wells, "slots": slots} for rig in rigs],
        "slots": [{"name": slot, "wells": wells} for slot in slots],
        "wells_priority": {w: p for w, p in wells_priority},
    }
    return config


def _delayed_advanced_setup():
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

    return config


def verify_priority(schedule, config):
    for task1 in schedule:
        for task2 in schedule:
            priority1 = dict(config.wells_priority)[task1.well]
            priority2 = dict(config.wells_priority)[task2.well]
            if task1.start_date > task2.start_date:
                assert priority1 <= priority2


def test_simple_well_order():
    config = _simple_setup().snapshot
    well_order = [("W1", datetime(2000, 1, 1)), ("W2", datetime(2000, 1, 6))]
    schedule = evaluate(config)

    schedule_well_order = [(event.well, event.start_date) for event in schedule]

    assert len(schedule) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)

    assert not verify_constraints(create_config_dictionary(config), schedule)


def test_wrong_schedule():
    config_snapshot = get_drill_planner_config_snapshot(_advanced_setup())
    schedule = evaluate(config_snapshot)

    # mess with the schedule/config to induce constraint violations
    config = _advanced_setup()
    for rig in config["rigs"]:
        if rig["name"] == "C":
            rig["slots"] = rig["slots"][1:]
        if rig["name"] == "A":
            rig["unavailability"] = [
                {"start": config["start_date"], "stop": config["end_date"]}
            ]
    for slot in config["slots"]:
        if slot["name"] == "S5":
            slot["unavailability"] = [
                {"start": config["start_date"], "stop": config["end_date"]}
            ]

    config_snapshot = get_drill_planner_config_snapshot(config)

    schedule[0] = schedule[0]._replace(
        slot="S1", start_date=datetime(1900, 1, 1), end_date=datetime(2100, 1, 1)
    )
    schedule[1] = schedule[1]._replace(slot="S5", well="W5")
    schedule[2] = schedule[2]._replace(slot="S1")

    expected_error_list = [
        (
            "Task(rig=B, slot=S1, well=W1, start=1900-01-01, end=2100-01-01) "
            "starts before config start date."
        ),
        (
            "Task(rig=B, slot=S1, well=W1, start=1900-01-01, end=2100-01-01) "
            "ends after config end date."
        ),
        (
            "Well W1's drilling time does not line up with that of "
            "Task(rig=B, slot=S1, well=W1, start=1900-01-01, end=2100-01-01)."
        ),
        "Task(rig=A, slot=S5, well=W5, start=2000-01-01, end=2000-01-31) represents an invalid drill combination",
        "Rig A or Slot S5 is unavailable during Task(rig=A, slot=S5, well=W5, start=2000-01-01, end=2000-01-31).",
        (
            "Well W5's drilling time does not line up with that of "
            "Task(rig=A, slot=S5, well=W5, start=2000-01-01, end=2000-01-31)."
        ),
        "Task(rig=C, slot=S1, well=W3, start=2000-01-01, end=2000-01-26) represents an invalid drill combination",
        "Well W5 was already drilled",
        (
            "Task(rig=B, slot=S1, well=W1, start=1900-01-01, end=2100-01-01) ends after "
            "Task(rig=B, slot=S4, well=W4, start=2000-01-11, end=2000-01-31) begins."
        ),
        "A slot is drilled through multiple times.",
    ]
    errors = verify_constraints(create_config_dictionary(config_snapshot), schedule)

    assert errors == expected_error_list


def test_rig_slot_reservation():
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

    config_snapshot = get_drill_planner_config_snapshot(_advanced_setup())
    well_order = [
        ("W1", datetime(2000, 1, 1), datetime(2000, 1, 11)),
        ("W2", datetime(2000, 1, 1), datetime(2000, 1, 31)),
        ("W3", datetime(2000, 1, 1), datetime(2000, 1, 26)),
        ("W4", datetime(2000, 1, 11), datetime(2000, 1, 31)),
        ("W5", datetime(2000, 1, 26), datetime(2000, 3, 6)),
    ]

    schedule = evaluate(config_snapshot)

    schedule_well_order = [
        (event.well, event.start_date, event.end_date) for event in schedule
    ]
    verify_priority(schedule, config_snapshot)

    assert len(schedule) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)

    assert not verify_constraints(create_config_dictionary(config_snapshot), schedule)


def test_rig_slot_include_delay():
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

    config = _delayed_advanced_setup()

    config_snapshot = get_drill_planner_config_snapshot(config)

    # WARNING: THIS IS RESULT OF A RUN
    # The results here show that the well priority constraint is given for start date, while it should
    # be for end date.
    """
    W1 is drilled first and must be drilled in rig A or B -> rig A unavailable thus W1 at B.
    W1 can be drilled in slot 3 and 5, but slot 3 must be used for W5. Thus W1, S5, B.

    W2 can be drilled in rig A and B. There's not enough time left in rig B to drill W2,
    before it becomes unavailable, thus W2 must be drilled at rig A. Rig A is unavailable
    till 2,5, hence drilling starts after that. W2 can be drill in any of S2, S4 and S1

    W3 can be drilled at all rigs, however Rig C is the only one that can drill W5. W4 can be drilled
    in rig B and C, however if Rig C should drill W5, rig B must drill W4. Hence W3 must be drilled at rig
    A. Rig A is drilling W2 until 3,6, which then is the new start date for W3.

    W3 has a short drill time than W4 (by 5 days) and thus W4 must be delayed if the order is to be
    preserved. W5 has longer drill times than W3, by 15 days, and hence drilling start of W5 can commence
    earlier.
    """
    detailed_well_order = [
        ("B", "W1", "S5", datetime(2000, 1, 1), datetime(2000, 1, 11)),
        ("A", "W2", "S4", datetime(2000, 2, 5), datetime(2000, 3, 6)),
        ("A", "W3", "S2", datetime(2000, 3, 6), datetime(2000, 3, 31)),
        ("B", "W4", "S1", datetime(2000, 3, 6), datetime(2000, 3, 26)),
        ("C", "W5", "S3", datetime(2000, 3, 6), datetime(2000, 4, 15)),
    ]

    well_order = [
        (well, start_date, end_date)
        for (_, well, _, start_date, end_date) in detailed_well_order
    ]

    schedule = evaluate(config_snapshot)

    schedule_well_order = [
        (event.well, event.start_date, event.end_date) for event in schedule
    ]
    verify_priority(schedule, config_snapshot)

    assert len(schedule) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)

    assert not verify_constraints(create_config_dictionary(config_snapshot), schedule)


@pytest.mark.slow
def test_default_large_setup():
    """
    Test that a larger setup without restrictions works

    We only verify that the output schedule pass the constraints
    given - the specific dates may change with versions of or-tools,
    and there may be multiple local minimums.
    """
    config_snapshot = get_drill_planner_config_snapshot(_large_setup())
    schedule = evaluate(config_snapshot)

    verify_priority(schedule, config_snapshot)
    assert not verify_constraints(create_config_dictionary(config_snapshot), schedule)


def test_invalid_config_schema():
    raw_config = _simple_config_setup()
    raw_config["rigs"][0]["unavailability"].append(
        {
            "start": raw_config["start_date"] - timedelta(days=10),
            "stop": raw_config["start_date"] + timedelta(days=10),
        }
    )
    config_suite = ConfigSuite(
        raw_config,
        drill_planner_schema.config_schema(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )

    assert not config_suite.valid

    raw_config = _simple_config_setup()
    raw_config["rigs"][0]["slots"].append("UNKNOWN_SLOT")
    config_suite = ConfigSuite(
        raw_config,
        drill_planner_schema.config_schema(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )

    assert not config_suite.valid

    raw_config = _simple_config_setup()
    raw_config["wells_priority"]["UNKNOWN_WELL"] = 10
    config_suite = ConfigSuite(
        raw_config,
        drill_planner_schema.config_schema(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )

    assert not config_suite.valid

    raw_config = _simple_config_setup()
    raw_config["slots"][1]["unavailability"].append(
        {
            "start": raw_config["start_date"] - timedelta(days=10),
            "stop": raw_config["start_date"] + timedelta(days=10),
        }
    )
    config_suite = ConfigSuite(
        raw_config,
        drill_planner_schema.config_schema(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )

    assert not config_suite.valid

    raw_config = _simple_config_setup()
    raw_config["slots"][1]["unavailability"].append(
        {
            "start": raw_config["start_date"] + timedelta(days=10),
            "stop": raw_config["end_date"] + timedelta(days=10),
        }
    )
    config_suite = ConfigSuite(
        raw_config,
        drill_planner_schema.config_schema(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )

    assert not config_suite.valid
