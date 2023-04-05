import functools

from hypothesis import strategies

from spinningjenny.jobs.fm_drill_planner.drillmodel import (
    DayRange,
    FieldManager,
    Rig,
    Slot,
    Well,
)
from spinningjenny.jobs.fm_drill_planner.ormodel import DrillConstraints
from spinningjenny.jobs.fm_drill_planner.utils import Event

SAMPLE_RANGE = 10
MAX_SIZE = 3

begin_day = strategies.integers(min_value=0, max_value=50)
end_day = strategies.integers(min_value=50, max_value=100)

unavailable_days = strategies.lists(
    strategies.builds(DayRange, begin_day, end_day),
    min_size=0,
    max_size=10,
    unique=True,
)

rig_name_samples, slot_name_samples, well_name_samples = (
    strategies.sampled_from([f"{prefix}{postfix}" for postfix in range(SAMPLE_RANGE)])
    for prefix in "RSW"
)

event = strategies.builds(
    Event,
    rig=rig_name_samples,
    slot=slot_name_samples,
    well=well_name_samples,
    begin=begin_day,
    end=end_day,
)

schedule = strategies.lists(event, unique_by=lambda x: (x.well, x.rig, x.slot))


def _parameter_strategies(max_size=3):
    return (
        strategies.builds(
            Rig,
            name=rig_name_samples,
            unavailable_ranges=unavailable_days,
            slot_wells=strategies.lists(
                strategies.tuples(
                    well_name_samples,
                    slot_name_samples,
                ),
                min_size=1,
                max_size=max_size,
                unique=True,
            ),
        ),
        strategies.builds(
            Slot,
            name=slot_name_samples,
            unavailable_ranges=unavailable_days,
            wells=strategies.lists(
                well_name_samples, min_size=1, max_size=max_size, unique=True
            ),
        ),
        strategies.builds(
            Well,
            name=well_name_samples,
            priority=strategies.integers(min_value=0, max_value=1000),
            drill_time=strategies.integers(min_value=1, max_value=15),
        ),
    )


list_strategy = functools.partial(
    strategies.lists,
    min_size=1,
    unique_by=lambda x: x.name,
    max_size=MAX_SIZE,
)


@strategies.composite
def field_manager(draw):
    rig, slot, well = _parameter_strategies()
    return draw(
        strategies.builds(
            FieldManager,
            rigs=list_strategy(elements=rig),
            slots=list_strategy(elements=slot),
            wells=list_strategy(elements=well),
            horizon=strategies.just(100),
        )
    )


def create_event(rig, slot, well, begin_day):
    return Event(rig, slot, well.name, begin_day, begin_day + well.drill_time)


def create_drill_constraints(rigs, slots, wells, horizon):
    return DrillConstraints(
        wells={well.name: well for well in wells},
        slots={slot.name: slot for slot in slots},
        rigs={rig.name: rig for rig in rigs},
        horizon=horizon,
    )


@strategies.composite
def constraints_assignment_pair(draw):
    rig, slot, well = _parameter_strategies()
    constraints = draw(
        strategies.builds(
            create_drill_constraints,
            wells=list_strategy(elements=well),
            slots=list_strategy(elements=slot),
            rigs=list_strategy(elements=rig),
            horizon=strategies.just(100),
        )
    )
    schedule = strategies.lists(
        strategies.builds(
            create_event,
            rig=strategies.sampled_from(list(constraints.rigs)),
            slot=strategies.sampled_from(list(constraints.slots)),
            well=strategies.sampled_from(list(constraints.wells.values())),
            begin_day=begin_day,
        ),
        unique_by=(lambda x: (x.rig, x.slot, x.well)),
    )

    return constraints, draw(schedule)
