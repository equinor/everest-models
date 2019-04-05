from collections import namedtuple
import copy
from datetime import datetime, timedelta
import math

from spinningjenny.drill_planner_optimization import evaluate
from spinningjenny.script.drill_planner import _verify_constraints, _verify_priority


def _simple_setup():
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2001, 1, 1)
    wells = ["W1", "W2"]
    rigs = ["A"]
    slots = ["S1", "S2"]
    config = {
        "rig_unavailability": {rig: [] for rig in rigs},
        "slot_unavailability": {slot: [] for slot in slots},
        "drill_time": {"W1": 5, "W2": 10},
        "wells": wells,
        "start_date": start_date,
        "end_date": end_date,
        "rigs": rigs,
        "slots": slots,
        "wells_at_rig": {"A": wells},
        "wells_at_slot": {"S1": wells, "S2": wells},
        "slots_at_rig": {"A": slots},
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
    rigs = ["A", "B", "C"]
    config = {
        "rig_unavailability": {rig: [] for rig in rigs},
        "slot_unavailability": {slot: [] for slot in slots},
        "drill_time": {"W1": 10, "W2": 30, "W3": 25, "W4": 20, "W5": 40},
        "wells": wells,
        "start_date": start_date,
        "end_date": end_date,
        "rigs": rigs,
        "slots": slots,
        "wells_at_rig": {"A": wells[:3], "B": wells[:4], "C": wells[2:]},
        "wells_at_slot": {
            "S1": wells[:4],
            "S2": wells[:4],
            "S3": wells,
            "S4": wells[:4],
            "S5": wells[:4],
        },
        "slots_at_rig": {"A": slots, "B": slots, "C": slots},
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
        "rig_unavailability": {rig: [] for rig in rigs},
        "slot_unavailability": {slot: [] for slot in slots},
        "drill_time": {w: drill_times[i] for i, w in enumerate(wells)},
        "wells": wells,
        "start_date": start_date,
        "end_date": end_date,
        "rigs": rigs,
        "slots": slots,
        "wells_at_rig": {r: wells for r in rigs},
        "wells_at_slot": {s: wells for s in slots},
        "slots_at_rig": {r: slots for r in rigs},
        "wells_priority": {w: p for w, p in wells_priority},
    }
    return config


def test_simple_well_order():
    config = _simple_setup()
    well_order = [("W1", datetime(2000, 1, 1)), ("W2", datetime(2000, 1, 6))]
    schedule = evaluate(**config)

    schedule_well_order = [(event.well, event.start_date) for event in schedule]

    assert len(schedule) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)

    _verify_constraints(config, schedule)


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
    config = _advanced_setup()
    well_order = [
        ("W1", datetime(2000, 1, 1), datetime(2000, 1, 11)),
        ("W2", datetime(2000, 1, 1), datetime(2000, 1, 31)),
        ("W3", datetime(2000, 1, 1), datetime(2000, 1, 26)),
        ("W4", datetime(2000, 1, 11), datetime(2000, 1, 31)),
        ("W5", datetime(2000, 1, 26), datetime(2000, 3, 6)),
    ]

    schedule = evaluate(**config)

    schedule_well_order = [
        (event.well, event.start_date, event.end_date) for event in schedule
    ]
    _verify_priority(schedule, config)

    assert len(schedule) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)

    _verify_constraints(config, schedule)


def test_rig_slot_inlude_delay():
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

    config = _advanced_setup()
    start_date = config["start_date"]

    # days after start each rig is unavailable
    unavailable = {"A": (0, 35), "B": (25, 43), "C": (32, 54)}

    config["rig_unavailability"] = {
        r: [
            [
                start_date + timedelta(days=unavailable[r][0]),
                start_date + timedelta(days=unavailable[r][1]),
            ]
        ]
        for r in config["rigs"]
    }

    # days after start each slot is unavailable
    unavailable = {
        "S1": (0, 10),
        "S2": (7, 14),
        "S3": (34, 43),  # drilling W5 must now be delayed
        "S4": (6, 18),
        "S5": (15, 18),
    }

    config["slot_unavailability"] = {
        s: [
            [
                start_date + timedelta(days=unavailable[s][0]),
                start_date + timedelta(days=unavailable[s][1]),
            ]
        ]
        for s in config["slots"]
    }
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

    schedule = evaluate(**config)

    schedule_well_order = [
        (event.well, event.start_date, event.end_date) for event in schedule
    ]
    _verify_priority(schedule, config)

    assert len(schedule) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)

    _verify_constraints(config, schedule)


def test_default_large_setup():
    """
    Test that a larger setup without restrictions works

    We only verify that the output schedule pass the constraints
    given - the specific dates may change with versions of or-tools,
    and there may be multiple local minimums.
    """
    config = _large_setup()

    schedule = evaluate(**config)

    _verify_priority(schedule, config)
    _verify_constraints(config, schedule)
