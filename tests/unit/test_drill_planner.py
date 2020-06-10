import collections

from datetime import datetime, timedelta
from configsuite import ConfigSuite
from ortools.sat.python import cp_model

from spinningjenny import load_yaml
from spinningjenny.script.fm_drill_planner import _prepare_config, _compare_schedules
from spinningjenny.drill_planner import (
    drill_planner_schema,
    resolve_priorities,
    ScheduleElement,
)
from spinningjenny.drill_planner.drillmodel import FieldManager, FieldSchedule
from spinningjenny.drill_planner.ormodel import run_optimization

from tests import tmpdir, relpath

TEST_DATA_PATH = relpath("tests", "testdata", "drill_planner")


def get_drill_planner_configsuite(config_dic):
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


def _simple_setup_config():
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
    return config


def _simple_setup():
    config_suite = get_drill_planner_configsuite(_simple_setup_config())

    return config_suite


def _small_setup_incl_unavailability_config():
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


def _small_setup_incl_unavailability():
    config_suite = get_drill_planner_configsuite(
        _small_setup_incl_unavailability_config()
    )

    return config_suite


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
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2005, 1, 1)
    wells = ["W" + str(i) for i in range(1, 30)]
    slots = ["S" + str(i) for i in range(1, 30)]
    rigs = ["A", "B", "C"]
    drill_times = [30, 20, 40, 25, 35, 75, 33, 90, 23, 32, 10, 42, 38, 47, 53]
    wells_priority = zip(wells, range(len(wells), 0, -1))
    config = {
        "start_date": start_date,
        "end_date": end_date,
        "wells": [
            {"name": w, "drill_time": drill_times[i % len(drill_times)]}
            for i, w in enumerate(wells)
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


def _build_config(raw_config):
    return ConfigSuite(
        raw_config,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
        deduce_required=True,
    )


def test_simple_well_order():
    config_snapshot = _simple_setup().snapshot
    well_order = [("W1", 0, 5), ("W2", 6, 16)]

    field_manager = FieldManager.generate_from_snapshot(config_snapshot)
    schedule = run_optimization(field_manager=field_manager)

    assert field_manager.valid_schedule(FieldSchedule(schedule))

    schedule_well_order = [(elem.well, elem.begin, elem.end) for elem in schedule]

    assert len(schedule) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)


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
        ("W1", 0, 10),
        ("W2", 0, 30),
        ("W3", 0, 25),
        ("W4", 11, 31),
        ("W5", 26, 66),
    ]

    field_manager = FieldManager.generate_from_snapshot(config_snapshot)
    schedule = run_optimization(field_manager=field_manager)

    assert field_manager.valid_schedule(FieldSchedule(schedule))

    schedule_well_order = [(elem.well, elem.begin, elem.end) for elem in schedule]
    assert len(schedule) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)


def test_rig_slot_include_delay():
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

    config = _delayed_advanced_setup()

    config_snapshot = get_drill_planner_config_snapshot(config)

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

    field_manager = FieldManager.generate_from_snapshot(config_snapshot)
    schedule = run_optimization(field_manager=field_manager)

    assert field_manager.valid_schedule(FieldSchedule(schedule))

    schedule_well_order = [(elem.well, elem.begin, elem.end) for elem in schedule]
    assert len(schedule) == len(well_order)
    assert all(test_task in schedule_well_order for test_task in well_order)
    assert all(schedule_task in well_order for schedule_task in schedule_well_order)


def test_default_large_setup():
    """
    Test that a larger setup without restrictions works

    We only verify that it is possible to set it up using or-tools, not that
    the solution itself is optimal.
    """
    config = _large_setup()
    config_snapshot = get_drill_planner_config_snapshot(config)

    field_manager = FieldManager.generate_from_snapshot(config_snapshot)
    schedule = run_optimization(
        field_manager=field_manager, solution_limit=1, accepted_status=cp_model.FEASIBLE
    )

    assert field_manager.valid_schedule(FieldSchedule(schedule))


def test_invalid_config_schema():
    raw_config = _small_setup_incl_unavailability_config()
    raw_config["rigs"][0]["unavailability"].append(
        {
            "start": raw_config["start_date"] - timedelta(days=10),
            "stop": raw_config["start_date"] + timedelta(days=10),
        }
    )
    config_suite = _build_config(raw_config)

    assert not config_suite.valid

    raw_config = _small_setup_incl_unavailability_config()
    raw_config["rigs"][0]["slots"].append("UNKNOWN_SLOT")
    config_suite = _build_config(raw_config)

    assert not config_suite.valid

    raw_config = _small_setup_incl_unavailability_config()
    raw_config["wells_priority"]["UNKNOWN_WELL"] = 10
    config_suite = _build_config(raw_config)

    assert not config_suite.valid

    raw_config = _small_setup_incl_unavailability_config()
    raw_config["slots"][1]["unavailability"].append(
        {
            "start": raw_config["start_date"] - timedelta(days=10),
            "stop": raw_config["start_date"] + timedelta(days=10),
        }
    )
    config_suite = _build_config(raw_config)

    assert not config_suite.valid

    raw_config = _small_setup_incl_unavailability_config()
    raw_config["slots"][1]["unavailability"].append(
        {
            "start": raw_config["start_date"] + timedelta(days=10),
            "stop": raw_config["end_date"] + timedelta(days=10),
        }
    )
    config_suite = _build_config(raw_config)

    assert not config_suite.valid


@tmpdir(TEST_DATA_PATH)
def test_script_prepare_config():
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
        ScheduleElement(rig=x[0], slot=x[1], well=x[2], begin=x[3], end=x[4])
        for x in well_order
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
        ScheduleElement(rig=x[0], slot=x[1], well=x[2], begin=x[3], end=x[4])
        for x in well_order
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
        ScheduleElement(rig=x[0], slot=x[1], well=x[2], begin=x[3], end=x[4])
        for x in well_order
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
        ScheduleElement(rig=x[0], slot=x[1], well=x[2], begin=x[3], end=x[4])
        for x in better_well_order
    ]
    assert better_schedule_list == _compare_schedules(
        schedule_list, better_schedule_list, wells_priority
    )


def assert_start_given(expected_begin, key, unavailabilities):
    config = _simple_setup_config()

    for idx, ranges in enumerate(unavailabilities):
        config[key][idx]["unavailability"] = [
            {
                "start": config["start_date"] + timedelta(days=begin),
                "stop": config["start_date"] + timedelta(days=end),
            }
            for (begin, end) in ranges
        ]

    config_snapshot = get_drill_planner_config_snapshot(config)

    field_manager = FieldManager.generate_from_snapshot(config_snapshot)
    schedule = run_optimization(field_manager=field_manager)

    assert field_manager.valid_schedule(FieldSchedule(schedule))
    assert schedule[0].begin == expected_begin


def test_inclusive_bounds_no_unavailability():
    config = _simple_setup_config()
    config_snapshot = get_drill_planner_config_snapshot(config)

    field_manager = FieldManager.generate_from_snapshot(config_snapshot)
    schedule = run_optimization(field_manager=field_manager)

    assert field_manager.valid_schedule(FieldSchedule(schedule))
    assert schedule[1].begin > schedule[0].end


def test_slot_unavailability_at_start():
    slot_one_unavailability = [(0, 0)]
    slot_two_unavailability = [(0, 0)]
    assert_start_given(
        expected_begin=1,
        key="slots",
        unavailabilities=[slot_one_unavailability, slot_two_unavailability],
    )


def test_slot_unavailability_insufficient_time_to_complete():
    slot_one_unavailability = [(5, 5)]
    slot_two_unavailability = [(5, 5)]
    assert_start_given(
        expected_begin=6,
        key="slots",
        unavailabilities=[slot_one_unavailability, slot_two_unavailability],
    )


def test_slot_unavailability_sufficient_time_to_complete():
    slot_one_unavailability = [(6, 6)]
    slot_two_unavailability = [(6, 6)]
    assert_start_given(
        expected_begin=0,
        key="slots",
        unavailabilities=[slot_one_unavailability, slot_two_unavailability],
    )


def test_slot_unavailability_insufficient_time_to_complete_between_unavailabilities():
    slot_one_unavailability = [(5, 5), (11, 11)]
    slot_two_unavailability = [(5, 5), (11, 11)]
    assert_start_given(
        expected_begin=12,
        key="slots",
        unavailabilities=[slot_one_unavailability, slot_two_unavailability],
    )


def test_slot_unavailability_sufficient_time_to_complete_between_unavailabilities():
    slot_one_unavailability = [(5, 5), (12, 12)]
    slot_two_unavailability = [(5, 5), (12, 12)]
    assert_start_given(
        expected_begin=6,
        key="slots",
        unavailabilities=[slot_one_unavailability, slot_two_unavailability],
    )


def test_rig_unavailability_at_start():
    rig_unavailability = [(0, 0)]
    assert_start_given(
        expected_begin=1, key="rigs", unavailabilities=[rig_unavailability]
    )


def test_rig_unavailability_insufficient_time_to_complete():
    rig_unavailability = [(5, 5)]
    assert_start_given(
        expected_begin=6, key="rigs", unavailabilities=[rig_unavailability]
    )


def test_rig_unavailability_sufficient_time_to_complete():
    rig_unavailability = [(6, 6)]
    assert_start_given(
        expected_begin=0, key="rigs", unavailabilities=[rig_unavailability]
    )


def test_rig_unavailability_insufficient_time_to_complete_between_unavailabilities():
    rig_unavailability = [(5, 5), (11, 11)]
    assert_start_given(
        expected_begin=12, key="rigs", unavailabilities=[rig_unavailability]
    )


def test_rig_unavailability_sufficient_time_to_complete_between_unavailabilities():
    rig_unavailability = [(5, 5), (12, 12)]
    assert_start_given(
        expected_begin=6, key="rigs", unavailabilities=[rig_unavailability]
    )
