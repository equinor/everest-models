from itertools import combinations, product
from typing import Iterable, NamedTuple, Tuple

from spinningjenny.jobs.fm_drill_planner.utils import Event


def get_named_item_from_iterable(name, iterable):
    return next(filter(lambda x: x.name == name, iterable), None)


class Base:
    def __init__(self, name, unavailable_ranges):
        self.name = name
        self.unavailable_ranges = unavailable_ranges

    def available(self, day):
        return not any(range_.contains(day) for range_ in self.unavailable_ranges)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"name={self.name}"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Rig(Base):
    def __init__(self, name, unavailable_ranges, slot_wells):
        self.slot_wells = slot_wells
        super().__init__(name, unavailable_ranges)

    def can_drill(self, slot, well):
        return (slot, well) in self.slot_wells

    @property
    def wells(self) -> Tuple[str, ...]:
        return {well_name for _, well_name in self.slot_wells}

    def __str__(self):
        return f"Rig({super().__str__()}, slot_wells={self.slot_wells})"

    #         f"Rig(name='{self.name}', Slot_well pairs={len(self.slot_wells)}, "
    #         f"unavailabilites={len(self.unavailable_ranges)})"
    #     )


class Slot(Base):
    def __init__(self, name, unavailable_ranges, wells):
        self.wells = wells
        super().__init__(name, unavailable_ranges)

    def has_well(self, well):
        return well in self.wells

    def __str__(self):
        return f"Slot({super().__str__()}, wells={self.wells})"

    #         f"Slot(name='{self.name}', wells={len(self.wells)}, "
    #         f"unavailabilites={len(self.unavailable_ranges)})"
    #     )


class Well(NamedTuple):
    name: str
    priority: int
    drill_time: int


class DayRange:
    def __init__(self, begin, end):
        if begin > end:
            raise ValueError()
        self.begin = begin
        self.end = end

    def contains(self, day):
        return self.begin <= day <= self.end

    def overlaps(self, other):
        end_after = self.end >= other.begin
        start_before = self.begin <= other.end
        return end_after and start_before

    def overlaps_(self, begin, end):
        return self.end >= begin and self.begin <= end


class FieldManager:
    def __init__(self, rigs, slots, wells, horizon):
        self.wells = wells
        self.well_dict = {well.name: well for well in wells}
        self.rigs = rigs
        self.rig_dict = {rig.name: rig for rig in rigs}
        self.slots = slots
        self.slot_dict = {slot.name: slot for slot in slots}
        self.horizon = horizon

    @classmethod
    def generate_from_config(cls, rigs, slots, wells, horizon, **kwargs):
        def get_ranges(unavailability=None):
            if unavailability is None:
                unavailability = []
            return [DayRange(begin, end) for begin, end in unavailability]

        return cls(
            rigs=[
                Rig(
                    name=name,
                    unavailable_ranges=get_ranges(rig.get("unavailability")),
                    slot_wells=list(product(rig["slots"], rig["wells"])),
                )
                for name, rig in rigs.items()
            ],
            slots=[
                Slot(
                    name=name,
                    unavailable_ranges=get_ranges(slot.get("unavailability")),
                    wells=slot["wells"],
                )
                for name, slot in slots.items()
            ],
            wells=[Well(name=name, **well) for name, well in wells.items()],
            horizon=horizon,
        )

    @classmethod
    def set_schedule(cls, schedule):
        cls._schedule = schedule

    def get_well(self, name):
        return self.well_dict.get(name)

    def get_rig(self, name):
        return self.rig_dict.get(name)

    def get_slot(self, name):
        return self.slot_dict.get(name)

    def valid_schedule(self, schedule: Iterable[Event]):
        return all(
            (
                within_horizon(schedule, self.horizon),
                uses_same_wells(schedule, self.well_dict),
                uses_rigs_subset(schedule, self.rig_dict),
                uses_slots_subset(schedule, self.slot_dict),
                all_wells_drilled_once(schedule, self.wells),
                all_drill_times_valid(schedule, self.well_dict),
                no_rig_overlapping(schedule, self.rigs),
                all_rigs_available(schedule, self.rigs),
                all_slots_available(schedule, self.slots),
                all_elements_drillable(schedule, self.slot_dict, self.rig_dict),
                all_slots_atmost_once(schedule, self.slots),
            )
        )

    # def __repr__(self):
    #     return str(self)

    # def __str__(self):
    #     return (
    #         f"RigModel({len(self.rigs)} Rigs, {len(self.slots)} Slots, "
    #         f"{len(self.wells)} wells)"
    #     )


def within_horizon(schedule: Iterable[Event], horizon: int):
    return all(event.begin >= 0 and event.end <= horizon for event in schedule)


def uses_same_wells(schedule: Iterable[Event], well_dict: dict):
    return set(well_dict) == {event.well for event in schedule}


def uses_rigs_subset(schedule: Iterable[Event], rig_dict: dict):
    return {event.rig for event in schedule}.issubset(rig_dict)


def uses_slots_subset(schedule: Iterable[Event], slot_dict: dict):
    return {event.slot for event in schedule}.issubset(slot_dict)


def all_wells_drilled_once(schedule: Iterable[Event], wells: Iterable):
    return all(
        sum(element.well == well.name for element in schedule) == 1 for well in wells
    )


def all_slots_atmost_once(schedule: Iterable[Event], slots):
    return all(
        sum(element.slot == slot.name for element in schedule) <= 1 for slot in slots
    )


def all_drill_times_valid(schedule: Iterable[Event], well_dict):
    def _valid_time(elem):
        return (
            well := well_dict.get(elem.well)
        ) and elem.end - elem.begin == well.drill_time

    return all(_valid_time(elem) for elem in schedule)


def _is_available(begin, end, unavailable_ranges):
    return any(unavailable.overlaps_(begin, end) for unavailable in unavailable_ranges)


def all_rigs_available(schedule: Iterable[Event], rigs):
    return not any(
        _is_available(element.begin, element.end, rig.unavailable_ranges)
        for element in schedule
        for rig in rigs
        if element.rig == rig.name
    )


def all_slots_available(schedule: Iterable[Event], slots):
    return not any(
        _is_available(event.begin, event.end, slot.unavailable_ranges)
        for event in schedule
        for slot in slots
        if event.slot == slot.name
    )


def _is_drillable(rig, slot, event):
    return (
        all([rig, slot])
        and rig.can_drill(event.slot, event.well)
        and slot.has_well(event.well)
    )


def all_elements_drillable(schedule: Iterable[Event], slot_dict, rig_dict):
    return all(
        _is_drillable(rig_dict.get(elem.rig), slot_dict.get(elem.slot), elem)
        for elem in schedule
    )


def _is_rig_overlapping(rig, schedule: Iterable[Event]):
    return any(
        DayRange(elem1.begin, elem1.end).overlaps_(elem2.begin, elem2.end)
        for elem1, elem2 in combinations(filter(lambda x: x.rig == rig, schedule), 2)
    )


def no_rig_overlapping(schedule, rigs):
    return not any(_is_rig_overlapping(rig, schedule) for rig in rigs)
