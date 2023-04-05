import copy
import itertools
from itertools import combinations

import pytest
from configsuite import ConfigSuite
from hypothesis import given
from jobs.drill_planner.strategies import field_manager, schedule

from spinningjenny.jobs.fm_drill_planner import drill_planner_schema, drillmodel
from spinningjenny.jobs.fm_drill_planner.drillmodel import (
    DayRange,
    FieldManager,
    Rig,
    Slot,
)
from spinningjenny.jobs.fm_drill_planner.utils import Event


@given(schedule, field_manager())
def test_valid_schedules_must_drill_same_wells(schedule, model):
    assert (
        {model.get_well(event.well) for event in schedule} == set(model.wells)
    ) == drillmodel.uses_same_wells(schedule, model.well_dict)


@given(schedule, field_manager())
def test_valid_schedules_must_use_same_rigs(schedule, model):
    assert (
        {event.rig for event in schedule}.issubset(model.rigs)
    ) == drillmodel.uses_rigs_subset(schedule, model.rig_dict)


@given(schedule, field_manager())
def test_valid_schedules_must_use_same_slots(schedule, model):
    assert (
        {event.slot for event in schedule}.issubset(model.slots)
    ) == drillmodel.uses_slots_subset(schedule, model.slot_dict)


@given(schedule, field_manager())
def test_valid_schedules_drills_all_wells_once(schedule, model):
    if drillmodel.all_wells_drilled_once(schedule, model.wells):
        for well in model.wells:
            assert sum(event.well == well.name for event in schedule) == 1


@given(schedule, field_manager())
def test_valid_schedules_available_rigs(schedule, model):
    if drillmodel.all_rigs_available(schedule, model.rigs):
        for rig in model.rigs:
            for element in filter(lambda x: x.rig == rig, schedule):
                for day in range(element.begin, element.end + 1):
                    assert rig.available(day)
    else:
        assert any(
            any(
                any(
                    not rig.available(day)
                    for day in range(element.begin, element.end + 1)
                )
                for element in filter(lambda x: x.rig == rig, schedule)
            )
            for rig in model.rigs
        )


@given(schedule, field_manager())
def test_valid_schedules_available_slots(schedule, model):
    if drillmodel.all_slots_available(schedule, model.slots):
        for slot in model.slots:
            for element in filter(lambda x: x.slot == slot, schedule):
                for day in range(element.begin, element.end + 1):
                    assert slot.available(day)
    else:
        assert any(
            any(
                any(
                    not slot.available(day)
                    for day in range(element.begin, element.end + 1)
                )
                for element in filter(lambda x: x.slot == slot, schedule)
            )
            for slot in model.slots
        )


@given(schedule, field_manager())
def test_valid_schedules_rig_can_drill_element(schedule, model):
    if drillmodel.all_elements_drillable(schedule, model.slot_dict, model.rig_dict):
        for event in schedule:
            rig = model.rig_dict.get(event.rig)
            slot = model.slot_dict.get(event.slot)
            well = model.well_dict.get(event.well)
            assert rig.can_drill(well, slot) and slot.has_well(well)
    else:
        not_drillable = []
        for element in schedule:
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


@given(schedule, field_manager())
def test_non_overlapping_rigs(schedule, model):
    assert drillmodel.no_rig_overlapping(schedule, model.rigs) == (
        all(
            all(
                not DayRange(e1.begin, e1.end).overlaps(DayRange(e2.begin, e2.end))
                for e1, e2 in combinations(filter(lambda x: x.rig == rig, schedule), 2)
            )
            for rig in model.rigs
        )
    )


@given(schedule, field_manager())
def test_valid_schedules_use_slots_only_once(schedule, model):
    if drillmodel.all_slots_atmost_once(schedule, model.slots):
        for slot in model.slots:
            assert sum(event.slot == slot for event in schedule) <= 1


def another_simple_setup(values, config):
    for key, value in values.items():
        config[key].update(value)
    return config


@pytest.mark.parametrize(
    "update_values",
    (
        {},
        {
            "rigs": {
                "UNUSED": {
                    "wells": ["W1"],
                    "slots": ["S1"],
                    "unavailability": [],
                    "delay": 0,
                }
            }
        },
        {"slots": {"UNUSED": {"wells": ["W1"], "unavailability": []}}},
    ),
)
def test_valid_schedule(update_values, simple_setup_config, rig_schedule):
    config = copy.deepcopy(simple_setup_config)
    for key, value in update_values.items():
        config[key].update(value)
    assert FieldManager.generate_from_config(**config).valid_schedule(rig_schedule)


def test_valid_simple_schedule(simple_field_manager, rig_schedule):
    assert simple_field_manager.valid_schedule(rig_schedule)


def test_invalid_schedule_drill_atleast_once(simple_config_wells):
    schedule = [Event(rig="A", slot="S1", well="W1", begin=0, end=5)]

    assert not drillmodel.all_wells_drilled_once(
        schedule, iter(simple_config_wells.values())
    )
    assert not drillmodel.uses_same_wells(schedule, simple_config_wells)


@pytest.mark.parametrize(
    "schedule",
    (
        pytest.param(
            (
                Event(rig="A", slot="S1", well="W1", begin=0, end=5),
                Event(rig="A", slot="S2", well="W2", begin=364, end=374),
            ),
            id="after end date",
        ),
        pytest.param(
            (
                Event(rig="A", slot="S1", well="W1", begin=-1, end=4),
                Event(rig="A", slot="S2", well="W2", begin=6, end=16),
            ),
            id="before start date",
        ),
    ),
)
def test_invalid_schedule_task(schedule, simple_config):
    assert not drillmodel.within_horizon(
        schedule, (simple_config["end_date"] - simple_config["start_date"]).days
    )


def test_invalid_schedule_used_more_than_once(config_snapshot):
    assert not drillmodel.all_slots_atmost_once(
        schedule=[
            Event(rig="A", slot="S1", well="W1", begin=0, end=5),
            Event(rig="A", slot="S1", well="W2", begin=6, end=16),
        ],
        slots=config_snapshot.slots,
    )


def test_invalid_schedule_unequal_drilltime(simple_config_wells):
    assert not drillmodel.all_drill_times_valid(
        schedule=[
            Event(rig="A", slot="S1", well="W1", begin=0, end=5),
            Event(rig="A", slot="S2", well="W2", begin=6, end=20),
        ],
        well_dict=simple_config_wells,
    )


@pytest.mark.parametrize(
    "schedule",
    (
        pytest.param(
            (
                Event(rig="A", slot="S1", well="W1", begin=0, end=5),
                Event(rig="B", slot="S3", well="W2", begin=6, end=20),
            ),
            id="rigs missing wells",
        ),
        pytest.param(
            (
                Event(rig="A", slot="S1", well="W2", begin=0, end=5),
                Event(rig="B", slot="S3", well="W1", begin=6, end=20),
            ),
            id="slots missing wells",
        ),
        pytest.param(
            (
                Event(rig="A", slot="S2", well="W2", begin=0, end=5),
                Event(rig="B", slot="S1", well="W1", begin=6, end=20),
            ),
            id="rigs missing slots",
        ),
    ),
)
def test_invalid_schedule_undrillable(schedule, simple_config):
    simple_config["rigs"].append({"name": "B", "wells": ["W1"], "slots": ["S3"]})
    simple_config["slots"].append({"name": "S3", "wells": ["W2"]})
    config_snapshot = ConfigSuite(
        simple_config,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
        deduce_required=True,
    ).snapshot

    assert not drillmodel.all_elements_drillable(
        schedule,
        slot_dict={
            slot.name: Slot(
                slot.name,
                [
                    DayRange(
                        (period.start - config_snapshot.start_date).days,
                        (period.stop - config_snapshot.start_date).days,
                    )
                    for period in slot.unavailability
                ],
                slot.wells,
            )
            for slot in config_snapshot.slots
        },
        rig_dict={
            rig.name: Rig(
                rig.name,
                [
                    DayRange(
                        (period.start - config_snapshot.start_date).days,
                        (period.stop - config_snapshot.start_date).days,
                    )
                    for period in rig.unavailability
                ],
                list(itertools.product(rig.slots, rig.wells)),
            )
            for rig in config_snapshot.rigs
        },
    )


def test_invalid_schedule_rig_task_overlap(config_snapshot):
    assert not drillmodel.no_rig_overlapping(
        schedule=[
            Event(rig="A", slot="S1", well="W1", begin=3, end=8),
            Event(rig="A", slot="S2", well="W2", begin=6, end=16),
        ],
        rigs=(
            Rig(
                rig.name,
                [
                    DayRange(
                        (period.start - config_snapshot.start_date).days,
                        (period.stop - config_snapshot.start_date).days,
                    )
                    for period in rig.unavailability
                ],
                list(itertools.product(rig.slots, rig.wells)),
            )
            for rig in config_snapshot.rigs
        ),
    )


def test_invalid_schedules_rig_unavailability(config_snapshot_unavailable):
    assert not drillmodel.all_rigs_available(
        schedule=[
            Event(rig="A", slot="S1", well="W1", begin=0, end=5),
            Event(rig="A", slot="S2", well="W2", begin=6, end=16),
        ],
        rigs=[
            Rig(
                rig.name,
                [
                    DayRange(
                        (period.start - config_snapshot_unavailable.start_date).days,
                        (period.stop - config_snapshot_unavailable.start_date).days,
                    )
                    for period in rig.unavailability
                ],
                list(itertools.product(rig.slots, rig.wells)),
            )
            for rig in config_snapshot_unavailable.rigs
        ],
    )


def test_invalid_schedules_slot_unavailability(config_snapshot_unavailable):
    assert not drillmodel.all_slots_available(
        schedule=[
            Event(rig="A", slot="S1", well="W1", begin=6, end=11),
            Event(rig="A", slot="S2", well="W2", begin=35, end=45),
        ],
        slots=[
            Slot(
                slot.name,
                [
                    DayRange(
                        (period.start - config_snapshot_unavailable.start_date).days,
                        (period.stop - config_snapshot_unavailable.start_date).days,
                    )
                    for period in slot.unavailability
                ],
                slot.wells,
            )
            for slot in config_snapshot_unavailable.slots
        ],
    )
