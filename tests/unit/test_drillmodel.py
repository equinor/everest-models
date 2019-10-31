from configsuite import ConfigSuite
from hypothesis import given, HealthCheck, settings
import hypothesis.strategies as st
from itertools import combinations

from spinningjenny.drill_planner.drillmodel import (
    FieldManager,
    FieldSchedule,
    Well,
    Rig,
    Slot,
    DayRange,
)

from tests.unit.test_drill_planner import (
    _small_setup_incl_unavailability,
    _simple_setup,
    _simple_setup_config,
)
from spinningjenny.drill_planner import drill_planner_schema, ScheduleElement

num_rigs = 10
num_wells = 10
num_slots = 10

days = st.integers(min_value=0, max_value=100)
priorities = st.integers(min_value=0, max_value=1000)


@st.composite
def day_ranges(draw, min_begin=0, max_begin=100, min_end=0, max_end=100):
    begin_day = draw(st.integers(min_value=min_begin, max_value=max_begin))
    end_day = draw(st.integers(min_value=max(begin_day, min_end), max_value=max_end))
    return DayRange(begin_day, end_day)


unavailable_days = st.lists(
    day_ranges(), min_size=0, max_size=10  # pylint: disable=no-value-for-parameter
)

wells = st.sampled_from(
    list(Well("W{}".format(i), priorities.example(), 1) for i in range(num_wells))
)

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


def create_schedule_element(rig, slot, well, begin, end):
    return ScheduleElement(rig.name, slot.name, well.name, begin, end)


@st.composite
def schedule_elements(draw, r=rigs, s=slots, w=wells):
    dr = draw(day_ranges())  # pylint: disable=no-value-for-parameter
    return draw(
        st.builds(create_schedule_element, r, s, w, st.just(dr.begin), st.just(dr.end))
    )


schedules = st.builds(
    FieldSchedule,
    st.lists(schedule_elements()),  # pylint: disable=no-value-for-parameter
)
field_managers = st.builds(
    FieldManager,
    st.lists(rigs, unique=True),
    st.lists(slots, unique=True),
    st.lists(wells, unique=True),
    st.just(100),
)


@settings(suppress_health_check=(HealthCheck.too_slow,))
@given(schedules, field_managers)
def test_valid_schedules_must_drill_same_wells(schedule, model):
    scheduled_wells = {model.get_well(w) for w in schedule.scheduled_wells}
    assert (scheduled_wells == set(model.wells)) == model.uses_same_wells(schedule)


@settings(suppress_health_check=(HealthCheck.too_slow,))
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


@settings(suppress_health_check=(HealthCheck.too_slow,))
@given(rigs, schedules)
def test_rig_elements(rig, schedule):
    for element in schedule.rig_elements(rig):
        assert element.rig == rig


@settings(suppress_health_check=(HealthCheck.too_slow,))
@given(slots, schedules)
def test_slot_elements(slot, schedule):
    for element in schedule.slot_elements(slot):
        assert element.slot == slot


@settings(suppress_health_check=(HealthCheck.too_slow,))
@given(schedules, field_managers)
def test_valid_schedules_available_rigs(schedule, model):
    if model.all_rigs_available(schedule):
        for rig in model.rigs:
            for element in schedule.rig_elements(rig):
                # should be range(element.begin, element.end + 1)
                for day in range(element.begin + 1, element.end):
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


@settings(suppress_health_check=(HealthCheck.too_slow,))
@given(schedules, field_managers)
def test_valid_schedules_available_slots(schedule, model):
    if model.all_slots_available(schedule):
        for slot in model.slots:
            for element in schedule.slot_elements(slot):
                # should be range(element.begin, element.end + 1)
                for day in range(element.begin + 1, element.end):
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


@settings(suppress_health_check=(HealthCheck.too_slow,))
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


# @given(day_ranges(), day_ranges())  # pylint: disable=no-value-for-parameter
# def test_overlap_implies_common_contains(a, b):
#   assert a.overlaps(b) == any(
#       a.contains(day) and b.contains(day) for day in range(a.begin, a.end + 1)
#   )


@settings(suppress_health_check=(HealthCheck.too_slow,))
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


@settings(suppress_health_check=(HealthCheck.too_slow,))
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
    )
    field_manager = FieldManager.generate_from_snapshot(config_suite.snapshot)
    assert field_manager.valid_schedule(rig_schedule)

    config = _simple_setup_config()
    config["slots"].append({"name": "UNUSED", "wells": ["W1"]})
    config_suite = ConfigSuite(
        config,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
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
