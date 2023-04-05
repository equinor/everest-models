import copy
import datetime
import functools
from copy import deepcopy

import pytest
from configsuite import ConfigSuite

from spinningjenny.jobs.fm_drill_planner import drill_planner_schema
from spinningjenny.jobs.fm_drill_planner.drillmodel import FieldManager
from spinningjenny.jobs.fm_drill_planner.ormodel import drill_constraint_model
from spinningjenny.jobs.fm_drill_planner.utils import Event

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

config_suite = functools.partial(
    ConfigSuite,
    schema=drill_planner_schema.build(),
    extract_validation_context=drill_planner_schema.extract_validation_context,
    deduce_required=True,
)


@pytest.fixture(scope="session")
def simple_setup_config():
    return {
        **MIN_CONFIG,
        "wells": WELLS,
        "rigs": {
            "A": {
                "wells": WELL_NAMES,
                "unavailability": [],
                "delay": 0,
                "slots": SLOT_NAMES,
            }
        },
        "slots": {
            slot: {
                "wells": WELL_NAMES,
                "unavailability": [],
            }
            for slot in SLOT_NAMES
        },
        "wells_priority": WELL_PRIORITIES,
    }


@pytest.fixture(scope="session")
def small_setup_incl_unavailability_config():
    return {
        **MIN_CONFIG,
        "rigs": {
            "A": {
                "wells": WELL_NAMES,
                "slots": SLOT_NAMES,
                "unavailability": [
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
                "unavailability": [
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
                "unavailability": [],
            },
            "S2": {
                "wells": WELL_NAMES,
                "unavailability": [
                    (
                        (datetime.date(2000, 2, 4) - START_DATE).days,
                        (datetime.date(2000, 2, 7) - START_DATE).days,
                    )
                ],
            },
        },
        "wells": WELLS,
        "wells_priority": WELL_PRIORITIES,
    }


@pytest.fixture(scope="session")
def advanced_setup():
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
                "unavailability": [],
            },
            "B": {
                "wells": wells[:4],
                "slots": slots,
                "delay": 0,
                "unavailability": [],
            },
            "C": {
                "wells": wells[2:],
                "slots": slots,
                "delay": 0,
                "unavailability": [],
            },
        },
        "slots": {
            "S1": {"wells": wells[:4], "unavailability": []},
            "S2": {"wells": wells[:4], "unavailability": []},
            "S3": {"wells": wells, "unavailability": []},
            "S4": {"wells": wells[:4], "unavailability": []},
            "S5": {"wells": wells[:4], "unavailability": []},
        },
        "wells_priority": well_priority,
    }


@pytest.fixture(scope="session")
def large_setup():
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
            w: {
                "drill_time": drill_times[i % len(drill_times)],
                "priority": wells_priority[w],
            }
            for i, w in enumerate(wells)
        },
        "rigs": {
            rig: {
                "wells": wells,
                "slots": slots,
                "delay": 0,
                "unavailability": [],
            }
            for rig in rigs
        },
        "slots": {slot: {"wells": wells, "unavailability": []} for slot in slots},
        "wells_priority": wells_priority,
    }


@pytest.fixture(scope="session")
def delayed_advanced_setup(advanced_setup):
    config = deepcopy(advanced_setup)

    # days after start each rig is unavailable
    unavailable = {"A": (0, 35), "B": (25, 43), "C": (32, 54)}

    for name, rig in config["rigs"].items():
        rig["unavailability"] = [(unavailable[name][0], unavailable[name][1])]

    # days after start each slot is unavailable
    unavailable = {
        "S1": (0, 10),
        "S2": (7, 14),
        "S3": (34, 43),  # drilling W5 must now be delayed
        "S4": (6, 18),
        "S5": (15, 18),
    }

    for name, slot in config["slots"].items():
        slot["unavailability"] = [(unavailable[name][0], unavailable[name][1])]

    return config


@pytest.fixture
def advanced_field_manager(advanced_setup):
    return FieldManager.generate_from_config(**advanced_setup)


@pytest.fixture
def advanced_drill_constraints_model(advanced_field_manager):
    return drill_constraint_model(
        advanced_field_manager.well_dict,
        advanced_field_manager.slot_dict,
        advanced_field_manager.rig_dict,
        advanced_field_manager.horizon,
    )


@pytest.fixture
def simple_field_manager(simple_setup_config):
    return FieldManager.generate_from_config(**simple_setup_config)


@pytest.fixture
def simple_drill_constraints_model(simple_field_manager):
    return drill_constraint_model(
        simple_field_manager.well_dict,
        simple_field_manager.slot_dict,
        simple_field_manager.rig_dict,
        simple_field_manager.horizon,
    )


@pytest.fixture
def large_field_manager(large_setup):
    return FieldManager.generate_from_config(**large_setup)


@pytest.fixture
def large_drill_constraints_model(large_field_manager):
    return drill_constraint_model(
        large_field_manager.well_dict,
        large_field_manager.slot_dict,
        large_field_manager.rig_dict,
        large_field_manager.horizon,
    )


@pytest.fixture
def delayed_field_manager(delayed_advanced_setup):
    return FieldManager.generate_from_config(**delayed_advanced_setup)


@pytest.fixture
def delayed_drill_constraints_model(delayed_field_manager):
    return drill_constraint_model(
        delayed_field_manager.well_dict,
        delayed_field_manager.slot_dict,
        delayed_field_manager.rig_dict,
        delayed_field_manager.horizon,
    )


@pytest.fixture(scope="module")
def simple_config():
    wells = ["W1", "W2"]
    slots = ["S1", "S2"]
    return {
        "start_date": datetime.date(2000, 1, 1),
        "end_date": datetime.date(2001, 1, 1),
        "wells": [{"name": "W1", "drill_time": 5}, {"name": "W2", "drill_time": 10}],
        "rigs": [{"name": "A", "wells": wells, "slots": slots}],
        "slots": [{"name": slot, "wells": wells} for slot in slots],
        "wells_priority": {"W1": 1, "W2": 0.5},
    }


@pytest.fixture(scope="module")
def config_unavailable(simple_config):
    config = copy.deepcopy(simple_config)
    wells = [well["name"] for well in config["wells"]]
    start = datetime.date(2000, 2, 4)
    stop = datetime.date(2000, 2, 7)
    config["rigs"][0]["unavailability"] = [
        {
            "start": datetime.date(2000, 1, 3),
            "stop": datetime.date(2000, 1, 5),
        }
    ]
    config["rigs"].append(
        {
            "name": "B",
            "wells": wells,
            "slots": [slot["name"] for slot in simple_config["slots"]],
            "unavailability": [
                {
                    "start": start,
                    "stop": stop,
                }
            ],
        }
    )
    config["slots"][1]["unavailability"] = [
        {
            "start": start,
            "stop": stop,
        }
    ]
    return config


@pytest.fixture(scope="module")
def config_snapshot_unavailable(config_unavailable):
    return config_suite(config_unavailable).snapshot


@pytest.fixture(scope="module")
def config_snapshot(simple_config):
    return config_suite(simple_config).snapshot


@pytest.fixture(scope="module")
def simple_config_wells(config_snapshot):
    return {well.name: well for well in config_snapshot.wells}


@pytest.fixture(scope="module")
def rig_schedule():
    return [
        Event(rig="A", slot="S1", well="W1", begin=0, end=5),
        Event(rig="A", slot="S2", well="W2", begin=6, end=16),
    ]
