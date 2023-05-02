import string

from hypothesis import strategies

# from spinningjenny.jobs.fm_drill_planner.manager import get_field_manager
from spinningjenny.jobs.fm_drill_planner.data import (
    DayRange,
    Event,
    Rig,
    Slot,
    WellPriority,
)
from spinningjenny.jobs.fm_drill_planner.planner.optimized import _DrillConstraints

MAX_SIZE = 3
MIN_SIZE = 1

begin_day = strategies.integers(min_value=0, max_value=50)
end_day = strategies.integers(min_value=50, max_value=100)

day_ranges = strategies.lists(
    strategies.builds(DayRange, begin_day, end_day),
    min_size=0,
    max_size=10,
    unique=True,
)


@strategies.composite
def constraints_schedule(draw):
    wells = draw(
        strategies.dictionaries(
            keys=strategies.text(string.ascii_letters, max_size=8, min_size=6),
            values=strategies.builds(
                WellPriority,
                priority=strategies.integers(min_value=0, max_value=1000),
                drill_time=strategies.integers(min_value=1, max_value=15),
            ),
            max_size=MAX_SIZE,
            min_size=MAX_SIZE,
        )
    )
    well_names = tuple(wells)
    slots = draw(
        strategies.dictionaries(
            keys=strategies.text(string.ascii_letters, max_size=8, min_size=6),
            values=strategies.builds(
                Slot,
                wells=strategies.lists(
                    strategies.sampled_from(well_names), max_size=3, min_size=1
                ),
                day_ranges=day_ranges,
            ),
            min_size=MIN_SIZE,
            max_size=MAX_SIZE,
        )
    )
    slot_names = tuple(slots)
    rigs = draw(
        strategies.dictionaries(
            keys=strategies.text(string.ascii_letters, max_size=8, min_size=6),
            values=strategies.builds(
                Rig,
                wells=strategies.lists(
                    strategies.sampled_from(slot_names), max_size=3, min_size=1
                ),
                slots=strategies.lists(
                    strategies.sampled_from(slot_names), max_size=3, min_size=1
                ),
                day_ranges=day_ranges,
            ),
            min_size=MIN_SIZE,
            max_size=MAX_SIZE,
        )
    )
    rig_names = tuple(rigs)

    def create_event(rig, slot, well, begin_day):
        _well = wells[well]
        return Event(rig, slot, well, begin_day, begin_day + _well.drill_time)

    schedule = draw(
        strategies.lists(
            strategies.builds(
                create_event,
                rig=strategies.sampled_from(rig_names),
                slot=strategies.sampled_from(slot_names),
                well=strategies.sampled_from(well_names),
                begin_day=begin_day,
            ),
            unique_by=(lambda x: (x.rig, x.slot, x.well)),
        )
    )
    return (
        _DrillConstraints(wells, rigs, slots, horizon=draw(strategies.just(100))),
        schedule,
    )
