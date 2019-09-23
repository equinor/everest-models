from collections import namedtuple
from itertools import combinations, product


class Rig:
    def __init__(self, name, unavailable_ranges, slot_wells):
        self.name = name
        self.unavailable_ranges = unavailable_ranges
        self.slot_wells = slot_wells

    def available(self, day):
        for r in self.unavailable_ranges:
            if r.contains(day):
                return False
        return True

    def can_drill(self, slot, well):
        return (slot.name, well.name) in self.slot_wells

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "Rig(name='{}', Slot_well pairs={}, unavailabilites={})".format(
            self.name, len(self.slot_wells), len(self.unavailable_ranges)
        )

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Slot:
    def __init__(self, name, unavailable_ranges, wells):
        self.name = name
        self.unavailable_ranges = unavailable_ranges
        self.wells = wells

    def available(self, day):
        for r in self.unavailable_ranges:
            if r.contains(day):
                return False
        return True

    def has_well(self, well):
        return well.name in self.wells

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "Slot(name='{}', wells={}, unavailabilites={})".format(
            self.name, len(self.wells), len(self.unavailable_ranges)
        )

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


Well = namedtuple("Well", ["name", "priority", "drill_time"])


class DayRange:
    def __init__(self, begin, end):
        if begin > end:
            raise ValueError()
        self.begin = begin
        self.end = end

    def contains(self, day):
        return self.begin <= day <= self.end

    def overlaps(self, other):
        # overlapping should be inclusive
        end_after = self.end > other.begin
        start_before = self.begin < other.end
        return end_after and start_before


class FieldManager:
    def __init__(self, rigs, slots, wells, horizon):
        self.wells = wells
        self.rigs = rigs
        self.slots = slots
        self.horizon = horizon

    @staticmethod
    def generate_from_snapshot(config):
        """
        This function only exists to generate the necessary initialization elements
        from a ConfigSuite snapshot, while having the FieldManager class as simple
        as possible which helps a great deal when testing.

        rig_model = FieldManager.generate_from_snapshot(config)

        """

        def _create_dayranges(key):
            # Should be refactored once ConfigSuite has default values
            if key.unavailability is None:
                return []

            return [
                DayRange(
                    (period.start - config.start_date).days,
                    (period.stop - config.start_date).days,
                )
                for period in key.unavailability
            ]

        wells_priority = {k: v for k, v in config.wells_priority}

        wells = [
            Well(name=w.name, priority=wells_priority[w.name], drill_time=w.drill_time)
            for w in config.wells
        ]

        slots = [
            Slot(name=s.name, unavailable_ranges=_create_dayranges(s), wells=s.wells)
            for s in config.slots
        ]

        rigs = [
            Rig(
                name=r.name,
                unavailable_ranges=_create_dayranges(r),
                slot_wells=list(product(r.slots, r.wells)),
            )
            for r in config.rigs
        ]
        horizon = (config.end_date - config.start_date).days

        return FieldManager(rigs=rigs, slots=slots, wells=wells, horizon=horizon)

    def within_horizon(self, schedule):
        return all(
            [elem.begin >= 0 and elem.end <= self.horizon for elem in schedule.elements]
        )

    def uses_same_wells(self, schedule):
        return set(self.wells) == set(schedule.scheduled_wells)

    def uses_rigs_subset(self, schedule):
        return set(schedule.scheduled_rigs).issubset(set(self.rigs))

    def uses_slots_subset(self, schedule):
        return set(schedule.scheduled_slots).issubset(set(self.slots))

    def all_wells_drilled_once(self, schedule):
        return all(len(list(schedule.well_elements(well))) == 1 for well in self.wells)

    def all_slots_atmost_once(self, schedule):
        return all(len(list(schedule.slot_elements(slot))) <= 1 for slot in self.slots)

    def all_drill_times_valid(self, schedule):
        return all(
            (elem.end - elem.begin == elem.well.drill_time)
            for elem in schedule.elements
        )

    def all_rigs_available(self, schedule):
        for rig in self.rigs:
            for elem in schedule.rig_elements(rig):
                if any(
                    unavailable.overlaps(elem.day_range)
                    for unavailable in rig.unavailable_ranges
                ):
                    return False
        return True

    def all_slots_available(self, schedule):
        for slot in self.slots:
            for elem in schedule.slot_elements(slot):
                if any(
                    unavailable.overlaps(elem.day_range)
                    for unavailable in slot.unavailable_ranges
                ):
                    return False
        return True

    def all_elements_drillable(self, schedule):
        return all(elem.is_drillable() for elem in schedule.elements)

    def no_rig_overlapping(self, schedule):
        for rig in self.rigs:
            elements = schedule.rig_elements(rig)
            for elem1, elem2 in combinations(elements, 2):
                if elem1.day_range.overlaps(elem2.day_range):
                    return False
        return True

    def valid_schedule(self, schedule):
        return all(
            [
                self.within_horizon(schedule),
                self.uses_same_wells(schedule),
                self.uses_rigs_subset(schedule),
                self.uses_slots_subset(schedule),
                self.all_wells_drilled_once(schedule),
                self.all_drill_times_valid(schedule),
                self.all_rigs_available(schedule),
                self.all_slots_available(schedule),
                self.all_elements_drillable(schedule),
                self.no_rig_overlapping(schedule),
                self.all_slots_atmost_once(schedule),
            ]
        )

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "RigModel({} Rigs, {} Slots, {} wells)".format(
            len(self.rigs), len(self.slots), len(self.wells)
        )


class ScheduleElement(
    namedtuple("ScheduleElement", ["well", "rig", "slot", "begin", "end"])
):
    @property
    def day_range(self):
        return DayRange(self.begin, self.end)

    def __str__(self):
        return "(rig: {}, slot: {}, well: {}, start: {}, end: {})".format(
            self.rig, self.slot, self.well, self.begin, self.end
        )

    def is_drillable(self):
        return self.rig.can_drill(self.slot, self.well) and self.slot.has_well(
            self.well
        )


def create_schedule_element(rigmodel, rig, slot, well, begin, end):
    return ScheduleElement(
        well=next(w for w in rigmodel.wells if w.name == well),
        rig=next(r for r in rigmodel.rigs if r.name == rig),
        slot=next(s for s in rigmodel.slots if s.name == slot),
        begin=begin,
        end=end,
    )


def create_schedule_events(rigmodel, schedule, start_date):
    return [
        create_schedule_element(
            rigmodel=rigmodel,
            rig=elem.rig,
            slot=elem.slot,
            well=elem.well,
            begin=(elem.start_date - start_date).days,
            end=(elem.end_date - start_date).days,
        )
        for elem in schedule
    ]


class FieldSchedule:
    def __init__(self, elements):
        self.elements = elements

    @property
    def scheduled_rigs(self):
        return list(set(x.rig for x in self.elements))

    @property
    def scheduled_slots(self):
        return list(set(x.slot for x in self.elements))

    @property
    def scheduled_wells(self):
        return list(set(x.well for x in self.elements))

    def rig_elements(self, rig):
        return (x for x in self.elements if x.rig == rig)

    def slot_elements(self, slot):
        return (x for x in self.elements if x.slot == slot)

    def well_elements(self, well):
        return (x for x in self.elements if x.well == well)
