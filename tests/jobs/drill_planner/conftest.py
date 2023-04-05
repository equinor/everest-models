import datetime

import pytest
from sub_testdata import DRILL_PLANNER as TEST_DATA

from spinningjenny.jobs.fm_drill_planner.manager.builder import FieldManagerBuilder
from spinningjenny.jobs.fm_drill_planner.models import Wells
from spinningjenny.jobs.shared.validators import valid_input_file

WELL_NAMES, SLOT_NAMES = ["W1", "W2"], ["S1", "S2"]
START_DATE, END_DATE = datetime.date(2000, 1, 1), datetime.date(2001, 1, 1)
WELL_PRIORITIES = {"W1": 1, "W2": 0.5}
WELLS = {
    "W1": {"drill_time": 5, "priority": WELL_PRIORITIES["W1"]},
    "W2": {"drill_time": 10, "priority": WELL_PRIORITIES["W2"]},
}
MIN_CONFIG = {
    "start_date": START_DATE,
    "end_date": END_DATE,
    "horizon": (END_DATE - START_DATE).days,
}


@pytest.fixture(scope="module")
def builder() -> FieldManagerBuilder:
    return FieldManagerBuilder()


@pytest.fixture(scope="module")
def small_wells_and_priority():
    return (
        Wells.parse_obj(
            [{"name": "W1", "drill_time": 5}, {"name": "W2", "drill_time": 10}]
        ),
        WELL_PRIORITIES,
    )


@pytest.fixture(scope="module")
def wells_and_priority(path_test_data):
    return (
        Wells.parse_obj(valid_input_file(path_test_data / TEST_DATA / "wells.json")),
        {"w1": 5, "w2": 4, "w3": 3, "w4": 2, "w5": 1},
    )


@pytest.fixture(scope="module")
def drill_planner_config(path_test_data):
    return valid_input_file(path_test_data / TEST_DATA / "config.yml")


@pytest.fixture(scope="session")
def simple_config():
    return {
        **MIN_CONFIG,
        "wells": WELLS,
        "rigs": {
            "A": {
                "wells": WELL_NAMES,
                "day_ranges": [],
                "delay": 0,
                "slots": SLOT_NAMES,
            }
        },
        "slots": {
            slot: {
                "wells": WELL_NAMES,
                "day_ranges": [],
            }
            for slot in SLOT_NAMES
        },
    }


@pytest.fixture(scope="session")
def small_config_include_day_ranges():
    return {
        **MIN_CONFIG,
        "rigs": {
            "A": {
                "wells": WELL_NAMES,
                "slots": SLOT_NAMES,
                "day_ranges": [
                    (
                        (datetime.date(2000, 1, 3) - START_DATE).days,
                        (datetime.date(2000, 1, 5) - START_DATE).days,
                    )
                ],
                "delay": 0,
            },
            "B": {
                "wells": WELL_NAMES,
                "slots": SLOT_NAMES,
                "day_ranges": [
                    (
                        (datetime.date(2000, 2, 4) - START_DATE).days,
                        (datetime.date(2000, 2, 7) - START_DATE).days,
                    )
                ],
                "delay": 0,
            },
        },
        "slots": {
            "S1": {
                "wells": WELL_NAMES,
                "day_ranges": [],
            },
            "S2": {
                "wells": WELL_NAMES,
                "day_ranges": [
                    (
                        (datetime.date(2000, 2, 4) - START_DATE).days,
                        (datetime.date(2000, 2, 7) - START_DATE).days,
                    )
                ],
            },
        },
        "wells": WELLS,
    }


@pytest.fixture(scope="session")
def advanced_config():
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
    wells = [*WELL_NAMES, "W3", "W4", "W5"]
    slots = [*SLOT_NAMES, "S3", "S4", "S5"]
    well_priority = {"W1": 5, "W2": 4, "W3": 3, "W4": 2, "W5": 1}
    return {
        **MIN_CONFIG,
        "wells": {
            "W1": {"drill_time": 10, "priority": well_priority["W1"]},
            "W2": {"drill_time": 30, "priority": well_priority["W2"]},
            "W3": {"drill_time": 25, "priority": well_priority["W3"]},
            "W4": {"drill_time": 20, "priority": well_priority["W4"]},
            "W5": {"drill_time": 40, "priority": well_priority["W5"]},
        },
        "rigs": {
            "A": {
                "wells": wells[:3],
                "slots": slots,
                "delay": 0,
                "day_ranges": [],
            },
            "B": {
                "wells": wells[:4],
                "slots": slots,
                "delay": 0,
                "day_ranges": [],
            },
            "C": {
                "wells": wells[2:],
                "slots": slots,
                "delay": 0,
                "day_ranges": [],
            },
        },
        "slots": {
            "S1": {"wells": wells[:4], "day_ranges": []},
            "S2": {"wells": wells[:4], "day_ranges": []},
            "S3": {"wells": wells, "day_ranges": []},
            "S4": {"wells": wells[:4], "day_ranges": []},
            "S5": {"wells": wells[:4], "day_ranges": []},
        },
    }


@pytest.fixture(scope="session")
def large_config():
    end_date = datetime.date(2025, 1, 1)
    wells = [f"W{i}" for i in range(1, 30)]
    slots = [f"S{i}" for i in range(1, 30)]
    rigs = ["A", "B", "C"]
    drill_times = [30, 20, 40, 25, 35, 75, 33, 90, 23, 32, 10, 42, 38, 47, 53]
    wells_priority = dict(zip(wells, range(len(wells), 0, -1)))
    return {
        "start_date": START_DATE,
        "end_date": end_date,
        "horizon": (end_date - START_DATE).days,
        "wells": {
            well: {
                "drill_time": drill_times[i % len(drill_times)],
                "priority": wells_priority[well],
            }
            for i, well in enumerate(wells)
        },
        "rigs": {
            rig: {
                "wells": wells,
                "slots": slots,
                "delay": 0,
                "day_ranges": [],
            }
            for rig in rigs
        },
        "slots": {slot: {"wells": wells, "day_ranges": []} for slot in slots},
    }
