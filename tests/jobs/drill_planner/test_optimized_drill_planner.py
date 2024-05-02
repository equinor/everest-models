from copy import deepcopy

import pytest
from everest_models.jobs.fm_drill_planner.data import (
    DayRange,
    Rig,
    Slot,
    WellPriority,
    validators,
)
from everest_models.jobs.fm_drill_planner.planner.optimized import (
    drill_constraint_model,
    run_optimization,
)
from hypothesis import assume, given
from jobs.drill_planner.strategies import constraints_schedule
from ortools.sat.python import cp_model


def task_schedule(schedule, well, rig, slot, task):
    if elements := [
        event
        for event in schedule
        if event.rig == rig and event.well == well and event.slot == slot
    ]:
        e = elements[0]
        if e.well != well or e.rig != rig or e.slot != slot:
            yield (task.presence, False)
        else:
            yield (task.presence, True)
            yield (task.begin, e.begin)
            yield (task.end, e.end)

    else:
        yield (task.presence, False)


def is_consistent(schedule):
    tasks = [(elem.rig, elem.slot, elem.well) for elem in schedule]
    return len(tasks) == len(set(tasks))


def apply_schedule(model, schedule):
    for (well, rig, slot), task in model.tasks.items():
        for var, value in task_schedule(schedule, well, rig, slot, task):
            if var.Name().startswith("end"):
                value += 1
            model.Add(var == value)


def satisfies(model, function_name, schedule):
    getattr(model, function_name)()
    apply_schedule(model, schedule)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    return status in [cp_model.FEASIBLE, cp_model.OPTIMAL]


@pytest.mark.parametrize(
    "schedule_validator, constraint_method, attribute, keys",
    (
        pytest.param(
            validators.no_rig_overlaps,
            "no_rig_overlapping",
            "rigs",
            True,
            id="no rig overlaps",
        ),
        pytest.param(
            validators.is_slot_available,
            "all_slots_available",
            "slots",
            False,
            id="is slot available",
        ),
        pytest.param(
            validators.is_rig_available,
            "all_rigs_available",
            "rigs",
            False,
            id="is rig available",
        ),
        pytest.param(
            validators.is_slots_at_most_once,
            "all_slots_atmost_once",
            "slots",
            True,
            id="slot is at most once",
        ),
        pytest.param(
            validators.is_well_drilled_once,
            "all_wells_drilled_once",
            "wells",
            True,
            id="well is drilled once",
        ),
    ),
)
@given(constraints_schedule())
def test_optimization_constraints(
    schedule_validator, constraint_method, attribute, keys, values
):
    constraints, schedule = values
    assume(is_consistent(schedule))
    input = getattr(constraints, attribute)

    assert (
        schedule_validator(schedule, iter(input) if keys else input)
        and validators.is_drill_time_valid(schedule, constraints.wells)
    ) == satisfies(constraints, constraint_method, schedule)


def _get_optimized_schedule(wells, slots, rigs, horizon, schedule=None, **_):
    return run_optimization(
        drill_constraint_model(
            wells={name: WellPriority(**kwargs) for name, kwargs in wells.items()},
            slots={name: Slot(**kwargs) for name, kwargs in slots.items()},
            rigs={name: Rig(**kwargs) for name, kwargs in rigs.items()},
            horizon=horizon,
            best_guess_schedule=schedule,
        ),
        3600,
    )


@pytest.mark.parametrize(
    "expected_begins, day_ranges",
    (
        pytest.param({"W1": 1}, {"S1": [(0, 0)], "S2": [(0, 0)]}, id="slot at start"),
        pytest.param(
            {"W1": 6},
            {"S1": [(5, 5)], "S2": [(5, 5)]},
            id="slot insufficient time",
        ),
        pytest.param(
            {"W1": 0},
            {"S1": [(6, 6)], "S2": [(6, 6)]},
            id="slot sufficient time",
        ),
        pytest.param(
            {"W1": 12},
            {"S1": [(5, 5), (11, 11)], "S2": [(5, 5), (11, 11)]},
            id="slot multi events insufficient time",
        ),
        pytest.param(
            {"W1": 6},
            {"S1": [(5, 5), (12, 12)], "S2": [(5, 5), (12, 12)]},
            id="slots multi events sufficient time",
        ),
        pytest.param({"W1": 1}, {"A": [(0, 0)]}, id="rig at start"),
        pytest.param({"W1": 6}, {"A": [(5, 5)]}, id="rig insufficient time"),
        pytest.param({"W1": 0}, {"A": [(6, 6)]}, id="rig sufficient time"),
        pytest.param(
            {"W1": 12},
            {"A": [(5, 5), (11, 11)]},
            id="rigs multi events insufficient time",
        ),
        pytest.param(
            {"W1": 6},
            {"A": [(5, 5), (12, 12)]},
            id="rigs multi events sufficient time",
        ),
    ),
)
def test_drill_planner_optimization_event_begin(
    expected_begins, day_ranges, simple_config
):
    config = deepcopy(simple_config)

    for attribute in ("slots", "rigs"):
        for id, value in config[attribute].items():
            if v := day_ranges.get(id):
                value["day_ranges"] = [DayRange(begin, end) for begin, end in v]

    schedule = _get_optimized_schedule(**config)
    assert all(
        event.begin == expected_begin
        for well_name, expected_begin in expected_begins.items()
        for event in schedule
        if event.well == well_name
    )


def test_inclusive_bounds_no_unavailability(simple_config):
    schedule = sorted(
        _get_optimized_schedule(**deepcopy(simple_config)),
        key=lambda element: simple_config["wells"][element.well]["priority"],
        reverse=True,
    )
    assert schedule[1].begin > schedule[0].end
