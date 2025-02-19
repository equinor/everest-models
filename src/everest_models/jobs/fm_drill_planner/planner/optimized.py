import functools
import itertools
import logging
from typing import Dict, Iterable, List, NamedTuple, Tuple

from ortools.sat.python import cp_model

from everest_models.jobs.fm_drill_planner.data import Event, Rig, Slot, WellPriority
from everest_models.jobs.fm_drill_planner.data.validators import can_be_drilled

logger = logging.getLogger(__name__)


class TaskType(NamedTuple):
    begin: cp_model.IntVar
    end: cp_model.IntVar
    presence: cp_model.IntVar  # bool (0, 1)
    interval: cp_model.IntervalVar


def _well_costs(wells: Iterable[str]) -> Dict[str, int]:
    """The difference between priorities of the wells can be quite small
    (e.g. W1: 0.83, W2: 0.84). We want to make sure that a lower priority
    well is only shifted prior to a higher priority well, if the higher
    priority is unaffected. We therefore sort the wells after priority and
    provide a significant increase in cost as priority is reduced
    """
    return {key: (index + 1) ** 4 for index, key in enumerate(wells)}


class _DrillConstraints(cp_model.CpModel):
    def __init__(
        self,
        wells: Dict[str, WellPriority],
        rigs: Dict[str, Rig],
        slots: Dict[str, Slot],
        horizon: int,
        best_guess_schedule: Iterable[Event] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.wells = wells
        self.rigs = rigs
        self.slots = slots
        self.horizon = horizon
        self.best_guess_schedule = best_guess_schedule
        self.tasks = self.create_tasks()
        self.well_cost = _well_costs(
            key for key, _ in sorted(wells.items(), key=lambda well: well[1].priority)
        )
        new_int_var = functools.partial(
            self.NewIntVar,
            0,
            sum(self.well_cost[well_name] for well_name in self.wells) * horizon,
        )
        self.rig_costs = {
            rig_name: new_int_var(f"{rig_name}_cost") for rig_name in self.rigs
        }
        self.objective = new_int_var("total_cost")
        self.single_wells_at_rig = self.create_single_rig_wells()

    def create_single_rig_wells(self) -> Dict[str, Tuple[str, ...]]:
        """
        Sets up the self.single_rig_tasks property.
        for each rig, self.single_rig_tasks[rig] is the list of
        tasks that can only performed by that rig.
        """

        return {
            name: (well_names if len(well_names := rig.wells) == 1 else ())
            for name, rig in self.rigs.items()
        }

    def create_tasks(self) -> Dict[Tuple[str, str, str], TaskType]:
        """
        There is a task associated with each well, rig, slot combination. The tasks
        will furthermore be used when setting constraints.
        """

        def task_type(name, drill_time):
            return TaskType(
                begin=(b := self.NewIntVar(0, self.horizon, f"begin_{name}")),
                end=(e := self.NewIntVar(0, self.horizon, f"end_{name}")),
                presence=(p := self.NewBoolVar(f"presence_{name}")),
                interval=self.NewOptionalIntervalVar(
                    b, drill_time + 1, e, p, f"interval_{name}"
                ),
            )

        return {
            (well_name, rig_name, slot_name): task_type(
                f"{well_name}_{rig_name}_{slot_name}", well.drill_time
            )
            for rig_name, slot_name, (well_name, well) in itertools.product(
                self.rigs,
                self.slots,
                self.wells.items(),
            )
        }

    def objective_function(self) -> None:
        for rig_name in self.rigs:
            self.Add(
                self.rig_costs[rig_name]
                == sum(
                    task.end * self.well_cost[well_name]
                    for (well_name, rig_name_, _), task in self.tasks.items()
                    if rig_name_ == rig_name
                )
            )
        self.Add(self.objective == sum(self.rig_costs.values()))
        self.Minimize(self.objective)

    def all_wells_drilled_once(self) -> None:
        """
        Adds a constraint enforcing that each well is drilled exactly once
        """
        for well_name in self.wells:
            self.Add(sum(task.presence for task in self.well_tasks(well_name)) == 1)

    def all_slots_atmost_once(self):
        """
        Adds a constraint enforcing that a slot can not be used more than once
        """
        for slot_name in self.slots:
            self.Add(sum(task.presence for task in self.slot_tasks(slot_name)) <= 1)

    def _unavailable_interval(
        self, name: str, begin: int, end: int
    ) -> cp_model.IntervalVar:
        return self.NewIntervalVar(
            begin,
            min(end + 1, self.horizon) - begin,
            min(end + 1, self.horizon),
            f"unavailable_{name}",
        )

    def _all_available(self, items, tasks) -> None:
        for key, value in items:
            unavailable_intervals = [
                self._unavailable_interval(key, r.begin, r.end)
                for r in value.day_ranges
            ]

            for task in tasks(key):
                for interval in unavailable_intervals:
                    self.AddNoOverlap([task.interval, interval])

    def all_rigs_available(self) -> None:
        """
        Adds constraint enforcing no rig performs a task overlapping
        with an interval in unavailable_intervals
        """
        self._all_available(self.rigs.items(), self.rig_tasks)

    def all_slots_available(self) -> None:
        """
        Adds constraint enforcing no slot is used to drill a well
        for any time period in slot_unavailability
        """
        self._all_available(self.slots.items(), self.slot_tasks)

    def no_rig_overlapping(self) -> None:
        """
        Adds a constraint enforcing that each rig drills
        only one well at the time
        """
        for rig_name in self.rigs:
            self.AddNoOverlap(task.interval for task in self.rig_tasks(rig_name))

    def all_wells_drillable(self) -> None:
        """
        Adds constraint enforcing that the well is drilled at
        a valid slot/rig combination
        """
        for key, task in self.tasks.items():
            if not can_be_drilled(*key, self.rigs, self.slots):
                self.Add(task.presence == 0)

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

    def _well_cost_sum(self, wells):
        return sum(
            self.well_cost[well_name] * drill_time
            for well_name, drill_time in zip(
                wells,
                itertools.accumulate(self.wells[well].drill_time + 1 for well in wells),
                strict=False,
            )
        )

    def add_redundant_constraints(self):
        """
        Adds a lower bound to each rig_costs. This lower bound is based on
        relaxing the problem to only drilling wells that can only be drilled by
        one rig and there is no unavailability. In that case the best solution
        is to drill the wells in prioritized order for each rig.
        """
        for rig_name in self.rigs:
            self.Add(
                self.rig_costs[rig_name]
                >= self._well_cost_sum(
                    sorted(
                        set(self.single_wells_at_rig[rig_name]).intersection(
                            self.wells
                        ),
                        key=lambda x: self.well_cost.get(x),
                        reverse=True,
                    )
                )
            )

    def add_hint_solution(self):
        if self.best_guess_schedule is None:
            return

        for event in self.best_guess_schedule:
            task = self.tasks[event.well, event.rig, event.slot]
            self.AddHint(task.begin, event.begin)
            self.AddHint(task.presence, True)

    def rig_tasks(self, rig_name):
        return (
            self.tasks[well_name, rig_name, slot_name]
            for well_name, slot_name in itertools.product(self.wells, self.slots)
        )

    def well_tasks(self, well_name):
        return (
            self.tasks[well_name, rig_name, slot_name]
            for rig_name, slot_name in itertools.product(self.rigs, self.slots)
        )

    def slot_tasks(self, slot_name):
        return (
            self.tasks[well_name, rig_name, slot_name]
            for rig_name, well_name in itertools.product(self.rigs, self.wells)
        )


class SolutionCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solution_count = 0
        self.__solution_limit = None

    def on_solution_callback(self):
        self.__solution_count += 1
        logger.info(
            "Solution found: Best bound: %f, new solution: %f",
            self.BestObjectiveBound(),
            self.ObjectiveValue(),
        )
        if self.__solution_limit and self.__solution_count >= self.__solution_limit:
            self.StopSearch()

    def solution_count(self):
        return self.__solution_count


def drill_constraint_model(wells, slots, rigs, horizon, best_guess_schedule=None):
    model = _DrillConstraints(
        wells=wells,
        slots=slots,
        rigs=rigs,
        horizon=horizon,
        best_guess_schedule=best_guess_schedule,
    )

    model.apply_constraints()
    model.objective_function()
    model.add_redundant_constraints()
    model.add_hint_solution()

    return model


def _create_event_schedule(tasks, solution):
    return [
        Event(
            rig=rig_name,
            slot=slot_name,
            well=well_name,
            begin=solution.Value(task.begin),
            end=solution.Value(task.end) - 1,
        )
        for (well_name, rig_name, slot_name), task in tasks.items()
        if solution.Value(task.presence)
    ]


def run_optimization(
    drill_constraint_model,
    max_time_seconds=3600,
) -> List[Event]:
    """Build a optimized list of events.

    Args:
        drill_constraint_model (_type_): CP-STAT model
        max_time_seconds (int, optional): solver's max time limit. Defaults to 3600.

    Returns:
        List[Event]: constraint optimized list of events
    """
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_time_seconds
    logger.debug("Solver set with maximum solve time of %f seconds", max_time_seconds)

    logger.info("Model statistics: %s", drill_constraint_model.ModelStats())
    logger.info("Optimization solver starting..")

    solution_printer = SolutionCallback()
    status = solver.Solve(drill_constraint_model, solution_callback=solution_printer)

    logger.debug("Solver completed with status: %s", solver.StatusName(status))
    logger.debug(
        "Detailed solver status: \n"
        "Number of conflicts: %d\n"
        "Number of solutions found: %d\n"
        "Objective Value: %d\n"
        "Walltime: %f\n",
        solver.NumConflicts(),
        solution_printer.solution_count(),
        solver.ObjectiveValue(),
        solver.WallTime(),
    )
    return (
        _create_event_schedule(drill_constraint_model.tasks, solver)
        if status == cp_model.OPTIMAL
        else []
    )
