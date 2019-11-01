from collections import namedtuple
from ortools.sat.python import cp_model
import itertools

from spinningjenny import customized_logger
from spinningjenny.drill_planner import ScheduleElement

logger = customized_logger.get_logger(__name__)

TaskType = namedtuple("TaskType", ("begin", "end", "presence", "interval"))


class DrillConstraints(cp_model.CpModel):
    def __init__(self, field_manager, *args, **kwargs):
        super(DrillConstraints, self).__init__(*args, **kwargs)
        self.field_manager = field_manager
        self.horizon = field_manager.horizon
        self.tasks = dict()
        self.create_tasks()

    def create_tasks(self):
        """
        There is a task associated with each well, rig, slot combination. The tasks
        will furthermore be used when setting constraints.
        """
        for rig, slot, well in itertools.product(
            self.field_manager.rigs, self.field_manager.slots, self.field_manager.wells
        ):
            begin_var = self.NewIntVar(
                0, self.horizon, "begin_{}_{}_{}".format(well.name, rig.name, slot.name)
            )

            end_var = self.NewIntVar(
                0, self.horizon, "end_{}_{}_{}".format(well.name, rig.name, slot.name)
            )

            presence_var = self.NewBoolVar(
                "presence_{}_{}_{}".format(well.name, rig.name, slot.name)
            )

            duration = well.drill_time + 1

            interval_var = self.NewOptionalIntervalVar(
                begin_var,
                duration,
                end_var,
                presence_var,
                "interval_{}_{}_{}".format(well.name, rig.name, slot.name),
            )

            self.tasks[well, rig, slot] = TaskType(
                begin=begin_var,
                end=end_var,
                interval=interval_var,
                presence=presence_var,
            )

            self.tasks[well, rig, slot]

    def objective_function(self):
        """
        The difference between priorities of the wells can be quite small
        (e.g. W1: 0.83, W2: 0.84). We want to make sure that a lower priority
        well is only shifted prior to a higher priority well, if the higher
        priority is unaffected. We therefore sort the wells after priority
        and provide an integer value that should suffice to keep that behaviour.
        """
        sorted_by_priority = sorted(self.field_manager.wells, key=lambda x: x.priority)
        wells_priority = {w: (i + 1) ** 5 for i, w in enumerate(sorted_by_priority)}

        objective = self.NewIntVar(0, 1000000000 * self.horizon, "makespan")
        self.Add(
            objective
            == sum(
                t.end * wells_priority[well]
                for (well, rig, slot), t in self.tasks.items()
            )
        )
        self.Minimize(objective)

    def all_wells_drilled_once(self):
        """
        Adds a constraint enforcing that each well is drilled exactly once
        """
        for well in self.field_manager.wells:
            present = [t.presence for t in self.well_tasks(well)]
            self.Add(sum(present) == 1)

    def all_slots_atmost_once(self):
        """
        Adds a constraint enforcing that a slot can not be used more than once
        """
        for slot in self.field_manager.slots:
            present = [t.presence for t in self.slot_tasks(slot)]
            self.Add(sum(present) <= 1)

    def all_rigs_available(self):
        """
        Adds constraint enforcing no rig performs a task overlapping
        with an interval in unavailable_intervals
        """
        for rig in self.field_manager.rigs:
            unavailable_intervals = [
                self.NewIntervalVar(
                    r.begin,
                    (min(r.end + 1, self.horizon) - r.begin),
                    min(r.end + 1, self.horizon),
                    "unavailable_{}".format(rig.name),
                )
                for r in rig.unavailable_ranges
            ]

            for task in self.rig_tasks(rig):
                for interval in unavailable_intervals:
                    self.AddNoOverlap([task.interval, interval])

    def all_slots_available(self):
        """
        Adds constraint enforcing no slot is used to drill a well
        for any time period in slot_unavailability
        """
        for slot in self.field_manager.slots:
            unavailable_intervals = [
                self.NewIntervalVar(
                    r.begin,
                    (min(r.end + 1, self.horizon) - r.begin),
                    min(r.end + 1, self.horizon),
                    "unavailable_{}".format(slot.name),
                )
                for r in slot.unavailable_ranges
            ]

            for task in self.slot_tasks(slot):
                for interval in unavailable_intervals:
                    self.AddNoOverlap([task.interval, interval])

    def no_rig_overlapping(self):
        """
        Adds a constraint enforcing that each rig drills
        only one well at the time
        """
        for rig in self.field_manager.rigs:
            intervals = [t.interval for t in self.rig_tasks(rig)]
            self.AddNoOverlap(intervals)

    def all_wells_drillable(self):
        """
        Adds constraint enforcing that the well is drilled at
        a valid slot/rig combination
        """
        for (well, rig, slot), t in self.tasks.items():
            if not rig.can_drill(slot.name, well.name) or not slot.has_well(well.name):
                self.Add(t.presence == 0)

    def apply_constraints(self):
        """
        Apply all constraints given by the field_manager
        """
        self.all_wells_drilled_once()
        self.all_slots_atmost_once()
        self.all_rigs_available()
        self.all_slots_available()
        self.no_rig_overlapping()
        self.all_wells_drillable()

    def rig_tasks(self, rig):
        for well, slot in itertools.product(
            self.field_manager.wells, self.field_manager.slots
        ):
            yield self.tasks[well, rig, slot]

    def well_tasks(self, well):
        for rig, slot in itertools.product(
            self.field_manager.rigs, self.field_manager.slots
        ):
            yield self.tasks[well, rig, slot]

    def slot_tasks(self, slot):
        for rig, well in itertools.product(
            self.field_manager.rigs, self.field_manager.wells
        ):
            yield self.tasks[well, rig, slot]


class SolutionCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solution_count = 0
        self.__solution_limit = limit

    def on_solution_callback(self):
        self.__solution_count += 1
        if self.__solution_limit and self.__solution_count >= self.__solution_limit:
            self.StopSearch()

    def solution_count(self):
        return self.__solution_count


def run_optimization(
    field_manager,
    max_solver_time=3600,
    solution_limit=None,
    accepted_status=cp_model.OPTIMAL,
):

    model = DrillConstraints(field_manager)

    model.apply_constraints()
    model.objective_function()

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_solver_time
    logger.debug(
        "Solver set with maximum solve time of {} seconds".format(max_solver_time)
    )

    logger.info("Optimization solver starting..")

    solution_printer = SolutionCallback(solution_limit)
    status = solver.SolveWithSolutionCallback(model, solution_printer)

    logger.debug("Solver completed with status: {}".format(solver.StatusName(status)))
    msg = (
        "Detailed solver status: \n"
        "Number of conflicts: {}\n"
        "Number of solutions found: {}\n"
        "Objective Value: {}\n"
        "Walltime: {}\n"
    )
    logger.debug(
        msg.format(
            solver.NumConflicts(),
            solver.ObjectiveValue(),
            solver.WallTime(),
            solution_printer.solution_count(),
        )
    )
    schedule = []
    if status == accepted_status:
        schedule = create_schedule_elements(model.tasks, solver)

    return schedule


def create_schedule_elements(tasks, solution):
    return [
        ScheduleElement(
            rig=rig.name,
            slot=slot.name,
            well=well.name,
            begin=solution.Value(t.begin),
            end=solution.Value(t.end) - 1,
        )
        for (well, rig, slot), t in tasks.items()
        if solution.Value(t.presence)
    ]
