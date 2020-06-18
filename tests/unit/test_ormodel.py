from hypothesis import given, assume
import hypothesis.strategies as st
from spinningjenny.drill_planner.ormodel import DrillConstraints
from spinningjenny.drill_planner.drillmodel import FieldSchedule
from spinningjenny.drill_planner import ScheduleElement

from tests.unit.test_drillmodel import field_managers, schedule_element, begin_day
from ortools.sat.python import cp_model


class Assignment(FieldSchedule):
    def task_assignments(self, well, rig, slot, task):
        elements = list(self.wrs_elements(well.name, rig.name, slot.name))
        if len(elements) == 0:
            yield (task.presence, False)
        else:
            e = elements[0]
            if e.well != well.name or e.rig != rig.name or e.slot != slot.name:
                yield (task.presence, False)
            else:
                yield (task.presence, True)
                yield (task.begin, e.begin)
                yield (task.end, e.end)

    def is_consistent(self):
        tasks = [(elem.rig, elem.slot, elem.well) for elem in self.elements]
        return len(tasks) == len(set(tasks))

    def wrs_elements(self, well, rig, slot):
        return set(
            x
            for x in self.elements
            if x.rig == rig and x.well == well and x.slot == slot
        )


well_drill_constraints = st.builds(DrillConstraints, field_managers)
assignments = st.builds(Assignment, st.lists(schedule_element, unique=True))


def create_schedule_elem(rig, slot, well, begin_day):
    return ScheduleElement(rig, slot, well.name, begin_day, begin_day + well.drill_time)


@st.composite
def constraints_assignment_pair(draw):
    constraints = draw(well_drill_constraints)

    wells = st.sampled_from(constraints.field_manager.wells)
    rigs = st.sampled_from([el.name for el in constraints.field_manager.rigs])
    slots = st.sampled_from([el.name for el in constraints.field_manager.slots])
    schedule_list = st.lists(
        st.builds(create_schedule_elem, rigs, slots, wells, begin_day),
        unique_by=(lambda x: (x.rig, x.slot, x.well)),
    )

    return constraints, Assignment(draw(schedule_list))


def apply_assignment(model, assignment):
    for (well, rig, slot), task in model.tasks.items():
        for var, value in assignment.task_assignments(well, rig, slot, task):
            if var.Name().startswith("end"):
                value += 1
            model.Add(var == value)


def satisfies(model, apply_constraints, assignment):
    apply_constraints()
    apply_assignment(model, assignment)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    return status == cp_model.FEASIBLE or status == cp_model.OPTIMAL


@given(well_drill_constraints, assignments)
def test_all_valid_schedules_are_consistent_assignments(constraints, assignment):

    field_manager = constraints.field_manager

    if field_manager.valid_schedule(assignment):
        assert assignment.is_consistent()


@given(constraints_assignment_pair())  # pylint: disable=no-value-for-parameter
def test_all_wells_drilled_once_constraints(pair):

    constraints, assignment = pair

    field_manager = constraints.field_manager

    domain_valid = field_manager.all_wells_drilled_once(
        assignment
    ) and field_manager.all_drill_times_valid(assignment)

    assume(assignment.is_consistent())

    or_valid = satisfies(constraints, constraints.all_wells_drilled_once, assignment)
    assert or_valid == domain_valid


@given(constraints_assignment_pair())  # pylint: disable=no-value-for-parameter
def test_all_slots_atmost_once_constraints(pair):

    constraints, assignment = pair

    field_manager = constraints.field_manager

    domain_valid = field_manager.all_slots_atmost_once(
        assignment
    ) and field_manager.all_drill_times_valid(assignment)

    assume(assignment.is_consistent())

    or_valid = satisfies(constraints, constraints.all_slots_atmost_once, assignment)
    assert or_valid == domain_valid


@given(constraints_assignment_pair())  # pylint: disable=no-value-for-parameter
def test_all_rigs_available_constraints(pair):

    constraints, assignment = pair

    field_manager = constraints.field_manager

    domain_valid = field_manager.all_rigs_available(
        assignment
    ) and field_manager.all_drill_times_valid(assignment)

    assume(assignment.is_consistent())

    or_valid = satisfies(constraints, constraints.all_rigs_available, assignment)
    assert or_valid == domain_valid


@given(constraints_assignment_pair())  # pylint: disable=no-value-for-parameter
def test_all_slots_available_constraints(pair):

    constraints, assignment = pair

    field_manager = constraints.field_manager

    domain_valid = field_manager.all_slots_available(
        assignment
    ) and field_manager.all_drill_times_valid(assignment)

    assume(assignment.is_consistent())

    or_valid = satisfies(constraints, constraints.all_slots_available, assignment)
    assert or_valid == domain_valid


@given(constraints_assignment_pair())  # pylint: disable=no-value-for-parameter
def test_no_rig_overlapping_constraints(pair):

    constraints, assignment = pair

    field_manager = constraints.field_manager

    domain_valid = field_manager.no_rig_overlapping(
        assignment
    ) and field_manager.all_drill_times_valid(assignment)

    assume(assignment.is_consistent())

    or_valid = satisfies(constraints, constraints.no_rig_overlapping, assignment)
    assert or_valid == domain_valid
