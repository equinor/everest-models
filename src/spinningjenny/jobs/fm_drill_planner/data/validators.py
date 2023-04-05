import itertools
from typing import Dict, Iterable, Tuple

from spinningjenny.jobs.fm_drill_planner.data._data import (
    Event,
    Rig,
    Slot,
    WellPriority,
)


def event_failed_conditions(
    schedule: Iterable[Event],
    wells: Dict[str, WellPriority],
    slots: Dict[str, Slot],
    rigs: Dict[str, Rig],
    horizon: int,
) -> bool:
    return (
        func.__name__.replace("_", " ")
        for func, parameters in (
            (is_within_horizon, (horizon,)),
            (uses_same_wells, (iter(wells),)),
            (is_rig_subset, (iter(rigs),)),
            (is_slot_subset, (iter(slots),)),
            (is_well_drilled_once, (iter(wells),)),
            (is_slots_at_most_once, (iter(slots),)),
            (is_rig_available, (rigs,)),
            (is_slot_available, (slots,)),
            (can_event_be_drilled, (rigs, slots)),
            (no_rig_overlaps, (iter(rigs),)),
            (is_drill_time_valid, (wells,)),
        )
        if not func(schedule, *parameters)
    )


def _is_event_available(
    begin: int, end: int, unavailable_range: Iterable[Tuple[int, int]]
) -> bool:
    return any(range.end >= begin and range.begin <= end for range in unavailable_range)


def is_within_horizon(schedule: Iterable[Event], horizon: int) -> bool:
    return all(event.begin >= 0 and event.end <= horizon for event in schedule)


def uses_same_wells(schedule: Iterable[Event], wells: Iterable[str]) -> bool:
    return not {event.well for event in schedule}.difference(wells)


def is_rig_subset(schedule: Iterable[Event], rigs: Iterable[str]) -> bool:
    return {event.rig for event in schedule}.issubset(rigs)


def is_slot_subset(schedule: Iterable[Event], slots: Iterable[str]) -> bool:
    return {event.slot for event in schedule}.issubset(slots)


def is_well_drilled_once(schedule: Iterable[Event], wells: Iterable[str]) -> bool:
    return all(sum(event.well == well for event in schedule) == 1 for well in wells)


def is_slots_at_most_once(schedule: Iterable[Event], slots: Iterable[str]) -> bool:
    return all(sum(event.slot == slot for event in schedule) <= 1 for slot in slots)


def is_rig_available(schedule: Iterable[Event], rigs: Dict[str, Rig]) -> bool:
    return not any(
        _is_event_available(event.begin, event.end, rig.day_ranges)
        for event in schedule
        for name, rig in rigs.items()
        if event.rig == name
    )


def is_slot_available(schedule: Iterable[Event], slots: Dict[str, Slot]) -> bool:
    return not any(
        _is_event_available(event.begin, event.end, slot.day_ranges)
        for event in schedule
        for name, slot in slots.items()
        if event.slot == name
    )


def can_be_drilled(
    well: str, rig: str, slot: str, rigs: Dict[str, Rig], slots: Dict[str, Slot]
) -> bool:
    return (slot, well) in rigs[rig].slot_well_product and well in slots[slot].wells


def can_event_be_drilled(
    schedule: Iterable[Event], rigs: Dict[str, Rig], slots: Dict[str, Slot]
) -> bool:
    return all(
        can_be_drilled(event.well, event.rig, event.slot, rigs, slots)
        for event in schedule
    )


def no_rig_overlaps(schedule: Iterable[Event], rigs: Iterable[str]) -> bool:
    def check_overlap(rig: str) -> bool:
        return any(
            event_a.overlaps(event_b.begin, event_b.end)
            for event_a, event_b in itertools.combinations(
                filter(lambda x: x.rig == rig, iter(schedule)), 2
            )
        )

    return not any(check_overlap(rig) for rig in rigs)


def is_drill_time_valid(
    schedule: Iterable[Event], wells: Dict[str, WellPriority]
) -> bool:
    def _is_valid_time(event: Event) -> bool:
        return (well := wells.get(event.well)) and event.drill_time == well.drill_time

    return all(_is_valid_time(event) for event in schedule)
