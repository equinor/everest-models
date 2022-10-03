from itertools import combinations

import hypothesis.strategies as st
from configsuite import ConfigSuite
from hypothesis import given
from jobs.drill_planner_.test_drill_planner import (
    _simple_setup,
    _simple_setup_config,
    _small_setup_incl_unavailability,
)

from jobs.fm_drill_planner import drill_planner_schema
from jobs.fm_drill_planner.drillmodel import (
    DayRange,
    FieldManager,
    FieldSchedule,
    Rig,
    Slot,
    Well,
)
from jobs.fm_drill_planner.utils import ScheduleElement

num_rigs = 10
num_wells = 10
num_slots = 10
priorities = st.integers(min_value=0, max_value=1000)

begin_day = st.integers(min_value=0, max_value=50)
end_day = st.integers(min_value=50, max_value=100)

day_range = st.builds(DayRange, begin_day, end_day)
unavailable_days = st.lists(day_range, min_size=0, max_size=10)

drill_time = st.integers(min_value=1, max_value=15)
rig_name = st.sampled_from(["R{}".format(i) for i in range(num_rigs)])
slot_name = st.sampled_from(["S{}".format(i) for i in range(num_slots)])
well_name = st.sampled_from(["W{}".format(i) for i in range(num_wells)])

wells = st.builds(Well, well_name, priorities, drill_time)


slots = st.sampled_from(
    list(
        Slot(
            "S{}".format(i),
            unavailable_days.example(),
            st.lists(wells, min_size=1).example(),
        )
        for i in range(num_slots)
    )
)

rigs = st.sampled_from(
    list(
        Rig(
            "R{}".format(i),
            unavailable_days.example(),
            list(
                zip(
                    st.lists(slots, min_size=1).example(),
                    st.lists(wells, min_size=1).example(),
                )
            ),
        )
        for i in range(num_rigs)
    )
)

schedule_element = st.builds(
    ScheduleElement, rig_name, slot_name, well_name, begin_day, end_day
)

schedules = st.builds(
    FieldSchedule,
    st.lists(schedule_element, unique=True),  # pylint: disable=no-value-for-parameter
)

field_managers = st.builds(
    FieldManager,
    st.lists(rigs, min_size=1, unique=True),
    st.lists(slots, min_size=1, unique=True),
    st.lists(wells, min_size=1, unique_by=lambda x: x.name),
    st.just(100),
)


@given(schedules, field_managers)
def test_valid_schedules_must_drill_same_wells(schedule, model):

    scheduled_wells = {model.get_well(w) for w in schedule.scheduled_wells}
    assert (scheduled_wells == set(model.wells)) == model.uses_same_wells(schedule)


@given(schedules, field_managers)
def test_valid_schedules_must_use_same_slots(schedule, model):
    assert (
        set(schedule.scheduled_rigs).issubset(set(model.rigs))
    ) == model.uses_rigs_subset(schedule)


@given(schedules, field_managers)
def test_valid_schedules_must_use_same_rigs(schedule, model):
    assert (
        set(schedule.scheduled_slots).issubset(set(model.slots))
    ) == model.uses_slots_subset(schedule)


@given(schedules, field_managers)
def test_valid_schedules_drills_all_wells_once(schedule, model):
    if model.all_wells_drilled_once(schedule):
        for well in model.wells:
            assert len(list(schedule.well_elements(well.name))) == 1


@given(rigs, schedules)
def test_rig_elements(rig, schedule):
    for element in schedule.rig_elements(rig):
        assert element.rig == rig


@given(slots, schedules)
def test_slot_elements(slot, schedule):
    for element in schedule.slot_elements(slot):
        assert element.slot == slot


@given(schedules, field_managers)
def test_valid_schedules_available_rigs(schedule, model):
    if model.all_rigs_available(schedule):
        for rig in model.rigs:
            for element in schedule.rig_elements(rig):
                for day in range(element.begin, element.end + 1):
                    assert rig.available(day)
    else:
        assert any(
            any(
                any(
                    not rig.available(day)
                    for day in range(element.begin, element.end + 1)
                )
                for element in schedule.rig_elements(rig)
            )
            for rig in model.rigs
        )


@given(schedules, field_managers)
def test_valid_schedules_available_slots(schedule, model):
    if model.all_slots_available(schedule):
        for slot in model.slots:
            for element in schedule.slot_elements(slot):
                for day in range(element.begin, element.end + 1):
                    assert slot.available(day)
    else:
        assert any(
            any(
                any(
                    not slot.available(day)
                    for day in range(element.begin, element.end + 1)
                )
                for element in schedule.slot_elements(slot)
            )
            for slot in model.slots
        )


@given(schedules, field_managers)
def test_valid_schedules_rig_can_drill_element(schedule, model):
    if model.all_elements_drillable(schedule):
        for element in schedule.elements:
            rig = model.get_rig(element.rig)
            slot = model.get_slot(element.slot)
            well = model.get_well(element.well)
            assert rig.can_drill(well, slot) and slot.has_well(well)
    else:
        not_drillable = []
        for element in schedule.elements:
            rig = model.get_rig(element.rig)
            slot = model.get_slot(element.slot)
            well = model.get_well(element.well)

            if not all([rig, slot, well]):
                not_drillable.append(True)
                continue

            not_drillable.append(
                not rig.can_drill(well, slot) or not slot.has_well(well)
            )
        assert any(not_drillable)


@given(schedules, field_managers)
def test_non_overlapping_rigs(schedule, model):
    assert model.no_rig_overlapping(schedule) == (
        all(
            all(
                not DayRange(e1.begin, e1.end).overlaps(DayRange(e2.begin, e2.end))
                for e1, e2 in combinations(schedule.rig_elements(rig), 2)
            )
            for rig in model.rigs
        )
    )


@given(schedules, field_managers)
def test_valid_schedules_use_slots_only_once(schedule, model):
    if model.all_slots_atmost_once(schedule):
        for slot in model.slots:
            assert len(list(schedule.slot_elements(slot))) <= 1


def test_valid_schedule():
    config_suite = _simple_setup()
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)
    schedule = [
        ScheduleElement(rig="A", slot="S1", well="W1", begin=0, end=5),
        ScheduleElement(rig="A", slot="S2", well="W2", begin=6, end=16),
    ]
    rig_schedule = FieldSchedule(schedule)
    assert field_manager.valid_schedule(rig_schedule)

    config = _simple_setup_config()
    config["rigs"].append({"name": "UNUSED", "wells": ["W1"], "slots": ["S1"]})
    config_suite = ConfigSuite(
        config,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
        deduce_required=True,
    )
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)
    assert field_manager.valid_schedule(rig_schedule)

    config = _simple_setup_config()
    config["slots"].append({"name": "UNUSED", "wells": ["W1"]})
    config_suite = ConfigSuite(
        config,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
        deduce_required=True,
    )
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)
    assert field_manager.valid_schedule(rig_schedule)


def test_invalid_schedule_drill_atleast_once():
    config_suite = _simple_setup()
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)

    schedule = [ScheduleElement(rig="A", slot="S1", well="W1", begin=0, end=5)]
    rig_schedule = FieldSchedule(schedule)

    assert not field_manager.all_wells_drilled_once(rig_schedule)
    assert not field_manager.uses_same_wells(rig_schedule)
    assert not field_manager.valid_schedule(rig_schedule)


def test_invalid_schedule_task_before_startdate():
    config_suite = _simple_setup()
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)
    schedule = [
        ScheduleElement(rig="A", slot="S1", well="W1", begin=-1, end=4),
        ScheduleElement(rig="A", slot="S2", well="W2", begin=6, end=16),
    ]
    rig_schedule = FieldSchedule(schedule)
    assert not field_manager.within_horizon(rig_schedule)
    assert not field_manager.valid_schedule(rig_schedule)


def test_invalid_schedule_task_after_enddate():
    config_suite = _simple_setup()
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)
    schedule = [
        ScheduleElement(rig="A", slot="S1", well="W1", begin=0, end=5),
        ScheduleElement(rig="A", slot="S2", well="W2", begin=364, end=374),
    ]
    rig_schedule = FieldSchedule(schedule)
    assert not field_manager.within_horizon(rig_schedule)
    assert not field_manager.valid_schedule(rig_schedule)


def test_invalid_schedule_used_more_than_once():
    config_suite = _simple_setup()
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)
    schedule = [
        ScheduleElement(rig="A", slot="S1", well="W1", begin=0, end=5),
        ScheduleElement(rig="A", slot="S1", well="W2", begin=6, end=16),
    ]
    rig_schedule = FieldSchedule(schedule)

    assert not field_manager.all_slots_atmost_once(rig_schedule)
    assert not field_manager.valid_schedule(rig_schedule)


def test_invalid_schedule_unequal_drilltime():
    config_suite = _simple_setup()
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)
    schedule = [
        ScheduleElement(rig="A", slot="S1", well="W1", begin=0, end=5),
        ScheduleElement(rig="A", slot="S2", well="W2", begin=6, end=20),
    ]
    rig_schedule = FieldSchedule(schedule)

    assert not field_manager.all_drill_times_valid(rig_schedule)
    assert not field_manager.valid_schedule(rig_schedule)


def test_invalid_schedule_undrillable():
    config = _simple_setup_config()
    config["rigs"].append({"name": "B", "wells": ["W1"], "slots": ["S3"]})
    config["slots"].append({"name": "S3", "wells": ["W2"]})
    config_suite = ConfigSuite(
        config,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
        deduce_required=True,
    )
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)

    # slot has well and rig has slot, but rig does not contain well
    schedule = [
        ScheduleElement(rig="A", slot="S1", well="W1", begin=0, end=5),
        ScheduleElement(rig="B", slot="S3", well="W2", begin=6, end=20),
    ]
    rig_schedule = FieldSchedule(schedule)

    assert not field_manager.all_elements_drillable(rig_schedule)
    assert not field_manager.valid_schedule(rig_schedule)

    # rig has slots and wells, but slot does not contain well
    schedule = [
        ScheduleElement(rig="A", slot="S1", well="W2", begin=0, end=5),
        ScheduleElement(rig="B", slot="S3", well="W1", begin=6, end=20),
    ]
    rig_schedule = FieldSchedule(schedule)

    assert not field_manager.all_elements_drillable(rig_schedule)
    assert not field_manager.valid_schedule(rig_schedule)

    # slot has well and rig has well, but rig does not contain slot
    schedule = [
        ScheduleElement(rig="A", slot="S2", well="W2", begin=0, end=5),
        ScheduleElement(rig="B", slot="S1", well="W1", begin=6, end=20),
    ]
    rig_schedule = FieldSchedule(schedule)

    assert not field_manager.all_elements_drillable(rig_schedule)
    assert not field_manager.valid_schedule(rig_schedule)


def test_invalid_schedule_rig_task_overlap():
    config_suite = _simple_setup()
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)
    schedule = [
        ScheduleElement(rig="A", slot="S1", well="W1", begin=3, end=8),
        ScheduleElement(rig="A", slot="S2", well="W2", begin=6, end=16),
    ]
    rig_schedule = FieldSchedule(schedule)

    assert not field_manager.no_rig_overlapping(rig_schedule)
    assert not field_manager.valid_schedule(rig_schedule)


def test_invalid_schedules_rig_unavailability():
    config_suite = _small_setup_incl_unavailability()
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)

    schedule = [
        ScheduleElement(rig="A", slot="S1", well="W1", begin=0, end=5),
        ScheduleElement(rig="A", slot="S2", well="W2", begin=6, end=16),
    ]
    rig_schedule = FieldSchedule(schedule)

    assert not field_manager.all_rigs_available(rig_schedule)
    assert not field_manager.valid_schedule(rig_schedule)


def test_invalid_schedules_slot_unavailability():
    config_suite = _small_setup_incl_unavailability()
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)
    # S2 unavailable from day 34 to 37
    schedule = [
        ScheduleElement(rig="A", slot="S1", well="W1", begin=6, end=11),
        ScheduleElement(rig="A", slot="S2", well="W2", begin=35, end=45),
    ]
    rig_schedule = FieldSchedule(schedule)

    assert not field_manager.all_slots_available(rig_schedule)
    assert not field_manager.valid_schedule(rig_schedule)
