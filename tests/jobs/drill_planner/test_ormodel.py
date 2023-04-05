from hypothesis import assume, given
from jobs.drill_planner.strategies import constraints_assignment_pair
from ortools.sat.python import cp_model

from spinningjenny.jobs.fm_drill_planner import drillmodel


def wrs_elements(schedule, well, rig, slot):
    return {x for x in schedule if x.rig == rig and x.well == well and x.slot == slot}


def task_assignments(schedule, well, rig, slot, task):
    if elements := list(wrs_elements(schedule, well, rig, slot)):
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


def apply_assignment(model, schedule):
    for (well, rig, slot), task in model.tasks.items():
        for var, value in task_assignments(schedule, well, rig, slot, task):
            if var.Name().startswith("end"):
                value += 1
            model.Add(var == value)


def satisfies(model, apply_constraints, schedule):
    apply_constraints()
    apply_assignment(model, schedule)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    return status in [cp_model.FEASIBLE, cp_model.OPTIMAL]


@given(constraints_assignment_pair())  # pylint: disable=no-value-for-parameter
def test_all_wells_drilled_once_constraints(pair):
    constraints, assignment = pair

    domain_valid = drillmodel.all_wells_drilled_once(
        assignment, constraints.wells.values()
    ) and drillmodel.all_drill_times_valid(assignment, constraints.wells)

    assume(is_consistent(assignment))

    or_valid = satisfies(constraints, constraints.all_wells_drilled_once, assignment)
    assert or_valid == domain_valid


@given(constraints_assignment_pair())  # pylint: disable=no-value-for-parameter
def test_all_slots_atmost_once_constraints(pair):
    constraints, assignment = pair

    domain_valid = drillmodel.all_slots_atmost_once(
        assignment, constraints.slots.values()
    ) and drillmodel.all_drill_times_valid(assignment, constraints.wells)

    assume(is_consistent(assignment))

    or_valid = satisfies(constraints, constraints.all_slots_atmost_once, assignment)
    assert or_valid == domain_valid


@given(constraints_assignment_pair())  # pylint: disable=no-value-for-parameter
def test_all_rigs_available_constraints(pair):
    constraints, assignment = pair

    domain_valid = drillmodel.all_rigs_available(
        assignment, constraints.rigs.values()
    ) and drillmodel.all_drill_times_valid(assignment, constraints.wells)

    assume(is_consistent(assignment))

    or_valid = satisfies(constraints, constraints.all_rigs_available, assignment)
    assert or_valid == domain_valid


@given(constraints_assignment_pair())  # pylint: disable=no-value-for-parameter
def test_all_slots_available_constraints(pair):
    constraints, assignment = pair

    domain_valid = drillmodel.all_slots_available(
        assignment, constraints.slots.values()
    ) and drillmodel.all_drill_times_valid(assignment, constraints.wells)

    assume(is_consistent(assignment))

    or_valid = satisfies(constraints, constraints.all_slots_available, assignment)
    assert or_valid == domain_valid


@given(constraints_assignment_pair())  # pylint: disable=no-value-for-parameter
def test_no_rig_overlapping_constraints(pair):
    constraints, assignment = pair

    domain_valid = drillmodel.no_rig_overlapping(
        assignment, constraints.rigs
    ) and drillmodel.all_drill_times_valid(assignment, constraints.wells)

    assume(is_consistent(assignment))

    or_valid = satisfies(constraints, constraints.no_rig_overlapping, assignment)
    assert or_valid == domain_valid
