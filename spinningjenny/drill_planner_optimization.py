import datetime
import collections
import itertools
from ortools.sat.python import cp_model

from spinningjenny import customized_logger

logger = customized_logger.get_logger(__name__)

TaskType = collections.namedtuple("TaskType", ("start", "end", "interval"))
ScheduleType = collections.namedtuple(
    "schedule_event", ("rig", "slot", "well", "start_date", "end_date")
)


class WellDrillScheduleModel(cp_model.CpModel):
    def __init__(
        self,
        wells,
        rigs,
        slots,
        drill_time,
        wells_at_rig,
        slots_at_rig,
        wells_at_slot,
        rig_unavailability,
        slot_unavailability,
        wells_priority,
        start_date,
        end_date,
    ):
        super(WellDrillScheduleModel, self).__init__()
        self._tasks = collections.defaultdict(dict)
        self._unavailable_intervals = collections.defaultdict(dict)
        self._well_ends = {}
        self._well_starts = {}
        self._task_before = collections.defaultdict(dict)
        self._task_after = collections.defaultdict(dict)
        self._not_drills = collections.defaultdict(dict)
        self.wells = wells
        self.rigs = rigs
        self.slots = slots
        self.slot_used = {
            slot: {
                well: self.NewBoolVar("slot_used_{}_{}".format(slot, well))
                for well in self.wells
            }
            for slot in self.slots
        }
        self._drill_time = drill_time
        self._horizon = (end_date - start_date).days
        self.start_date = start_date
        self.end_date = end_date
        self._objective_variable = self.NewIntVar(0, self._horizon, "makespan")
        self._rig_unavailability = rig_unavailability
        self._slot_unavailability = slot_unavailability
        self._wells_at_rig = wells_at_rig
        self._wells_at_slot = wells_at_slot
        self._slots_at_rig = slots_at_rig
        self._wells_priority = wells_priority

        self._setup_all_tasks()
        self._setup_unavailable_intervals()
        self._setup_well_ends()
        self._setup_well_starts()
        self._setup_tasks_before_after()
        self._setup_not_drills()

        self._no_overlap_rig_unavailable()
        self._enforce_slot_available()
        self._enforce_one_task_per_time_rig()
        self._enforce_one_task_per_well()
        self._enforce_well_at_slot()
        self._enforce_slot_at_rig()
        self._enforce_wells_priority()
        self._enforce_one_slot_assigned_to_well()
        self._enforce_slot_used_once()

        self._set_objective()

    def _setup_all_tasks(self):
        """
        There is a task associated with each well, rig pair. The task with the
        earliest start for each well is the actual drilling time for this well as each
        well only needs to be drilled once.
        """
        for well, rig in self.well_rig_pairs():
            start_var = self.NewIntVar(
                0, self._horizon, "start_{}_{}".format(well, rig)
            )
            duration = self._drill_time[well]
            end_var = self.NewIntVar(0, self._horizon, "end_{}_{}".format(well, rig))
            interval_var = self.NewIntervalVar(
                start_var, duration, end_var, "interval_{}_{}".format(well, rig)
            )

            self._tasks[well][rig] = TaskType(
                start=start_var, end=end_var, interval=interval_var
            )

    def _setup_unavailable_intervals(self):
        """
        Creates an IntervalVar for each range in rig_unavailability which can
        be added to a NoOverlap condition together with a task interval
        """
        for rig, ranges in self._rig_unavailability.items():
            result = []
            for start, stop in ranges:
                interval = self.NewIntervalVar(
                    (start - self.start_date).days,
                    (stop - start).days,
                    (stop - self.start_date).days,
                    "unavailable_{}".format(rig),
                )
                result.append(interval)
            self._unavailable_intervals[rig] = result

    def _setup_well_ends(self):
        """
        Creates an IntVar for each well specified. It represents the number
        of days from start to the completion of the well task.
        The variable is added as a minimalization:
        AddMinEquality(target, vars) -> Adds target == min(vars).
        """
        for well in self.wells:
            well_end = self.NewIntVar(0, self._horizon, "well_end_{}".format(well))
            self._well_ends[well] = well_end

            end_times = []
            for _, rig in self.well_rig_pairs(wells=[well]):
                task = self.task(well, rig)
                end_times.append(task.end)
            self.AddMinEquality(well_end, end_times)

    def _setup_well_starts(self):
        """
        Creates an IntVar for each well specified. It represents the number
        of days from start to the start of the well task.
        The variable is added as a minimalization:
        AddMinEquality(target, vars) -> Adds target == min(vars).
        """
        for well in self.wells:
            well_start = self.NewIntVar(0, self._horizon, "well_start_{}".format(well))
            self._well_starts[well] = well_start

            start_times = []
            for _, rig in self.well_rig_pairs(wells=[well]):
                task = self.task(well, rig)
                start_times.append(task.start)
            self.AddMinEquality(well_start, start_times)

    def _setup_tasks_before_after(self):
        """
        For every task, create variables for slot_unavailability.
        The variables can be used to define conditions to handle
        slot_unavailability
        """
        for well, rig in self.well_rig_pairs():
            self._setup_task_before_after(self._tasks[well][rig])

    def _setup_task_before_after(self, task):
        """
        For the given task, for every range in slot_unavailability,
        create boolean variables for each of the condition that
        the task is before the range, or a task is after the range.
        """
        for _, ranges in self._slot_unavailability.items():
            for start, end in ranges:
                start_index = (start - self.start_date).days
                task_before = self.NewBoolVar(
                    "task_before_{}_{}".format(task, start_index)
                )
                self.Add(task.end - start_index <= self._horizon * (1 - task_before))
                self._task_before[task][start] = task_before

                end_index = (end - self.start_date).days
                task_after = self.NewBoolVar("task_after_{}_{}".format(task, end_index))
                self.Add(end_index - task.start <= self._horizon * (1 - task_after))
                self._task_after[task][end] = task_after

    def _setup_not_drills(self):
        """
        Create a variable for each task that returns true if the task.well
        is not drilled at the task.rig.
        Adds a condition that if end date of the task is later than the
        end date of the well the well is not drilled at said rig.
        """
        for well, rig in self.well_rig_pairs():
            rig_not_drills = self.NewBoolVar("{}_not_drills_{}".format(rig, well))
            self._not_drills[rig][well] = rig_not_drills

            task = self.task(well, rig)
            self.Add(task.end - self._well_ends[well] >= rig_not_drills)

    def _set_objective(self):
        all_ends = []
        for well in self.wells:
            all_ends.append(self.well_end(well))
        self.AddMaxEquality(self._objective_variable, all_ends)
        self.Minimize(self._objective_variable)

    def well_rig_pairs(self, wells=None, rigs=None):
        """
        Iterable of all valid well, rig pairs

        Parameters
        ----------
        well : list
            list of well names
        rig : list
            list of rig names

        Returns
        ----------
        tuple
            yields a tuple of well, rig
        """

        if wells is None:
            wells = self.wells
        if rigs is None:
            rigs = self.rigs

        for well in wells:
            for rig in rigs:
                if well not in self._wells_at_rig[rig]:
                    continue
                yield (well, rig)

    def task(self, well, rig):
        """
        Parameters
        ----------
        well : str
            Name of the well
        rig : str
            Name of the rig

        Returns
        ----------
        TaskType
            The task associated with the well, rig pair.
        """
        return self._tasks[well][rig]

    def interval(self, well, rig):
        """
        Parameters
        ----------
        well : str
            Name of the well
        rig : str
            Name of the rig

        Returns
        ----------
        IntervalVar
            The interval associated with the well, rig pair
        """
        return self._tasks[well][rig].interval

    def unavailable_intervals(self, rig):
        """
        Parameters
        ----------
        rig : str
            Name of the rig

        Returns
        ----------
        list
            list of intervals where the rig is unavailable according
            to rig_unavailability.
        """
        return self._unavailable_intervals[rig]

    def well_end(self, well):
        """
        Parameters
        ----------
        well : str
            Name of the well

        Returns
        ----------
        IntVar
            variable representing the ending time for drilling the well.
        """
        return self._well_ends[well]

    def well_start(self, well):
        """
        Parameters
        ----------
        well : str
            Name of the well

        Returns
        ----------
        IntVar
            variable representing the starting time for drilling the well.
        """
        return self._well_starts[well]

    def task_before(self, task, start):
        """
        Parameters
        ----------
        task : TaskType
            The task to check for
        start : datetime
            The datetime object representing the start date to check for

        Returns
        ----------
        bool
            True if the task starts before the given time.
        """
        return self._task_before[task][start]

    def task_after(self, task, end):
        """
        Parameters
        ----------
        task : TaskType
            The task to check for
        end : datetime
            The datetime object representing the end date to check for

        Returns
        ----------
        bool
            True if the task starts before the given time.
        """
        return self._task_after[task][end]

    def not_drills(self, rig, well):
        """
        Parameters
        ----------
        well : str
            Name of the well
        rig : str
            Name of the rig

        Returns
        ----------
        bool
            True if the rig does not drill the well
        """
        return self._not_drills[rig][well]

    def _enforce_slot_at_rig(self):
        """
        Adds constraint that only slots in slots_at_rig is
        assigned to rigs for drilling any well at that slot.
        """
        for rig, rig_slots in self._slots_at_rig.items():
            for well, _ in self.well_rig_pairs(rigs=[rig]):
                for invalid_slot in set(self.slots) - set(rig_slots):
                    # Either the rig does not drill the well
                    # or the slot is not used for the well
                    self.AddBoolOr(
                        [
                            self.not_drills(rig, well),
                            self.slot_used[invalid_slot][well].Not(),
                        ]
                    )

    def _enforce_well_at_slot(self):
        """
        Adds constraint enforcing that a slot is not used for a
        well that is not in wells_at_slot.
        """
        for slot, well_slot in self._wells_at_slot.items():
            for invalid_well in set(self.wells) - set(well_slot):
                self.Add(self.slot_used[slot][invalid_well] == 0)

    def _enforce_one_task_per_time_rig(self):
        """
        Adds a constraint enforcing that each rig drills
        only one well at the time
        """
        for rig in self.rigs:
            intervals = [
                self.interval(well, rig) for well, _ in self.well_rig_pairs(rigs=[rig])
            ]
            self.AddNoOverlap(intervals)

    def _enforce_one_task_per_well(self):
        """
        Adds constraint enforcing no well is drilled twice at the
        same time.
        """
        for well in self.wells:
            intervals = [
                self.interval(well, rig) for _, rig in self.well_rig_pairs(wells=[well])
            ]
            self.AddNoOverlap(intervals)

    def _no_overlap_rig_unavailable(self):
        """
        Adds constraint enforcing no rig performs a task overlapping
        with an interval in unavailable_intervals
        """
        for well, rig in self.well_rig_pairs():
            task_interval = self.interval(well, rig)
            for unavailable_interval in self.unavailable_intervals(rig):
                self.AddNoOverlap([task_interval, unavailable_interval])

    def _enforce_slot_available(self):
        """
        Adds constraint enforcing no slot is used to drill a well
        for any time period in slot_unavailability
        """
        for slot, ranges in self._slot_unavailability.items():
            for start, stop in ranges:
                for well, rig in self.well_rig_pairs():
                    task = self.task(well, rig)
                    self.AddBoolOr(
                        [
                            self.task_before(task, start),
                            self.task_after(task, stop),
                            self.slot_used[slot][well].Not(),
                        ]
                    )

    def _enforce_wells_priority(self):
        """
        Enforces that well start drilling times are in the order of
        wells_priority
        """
        for (well1, well2) in itertools.combinations(self.wells, 2):
            if self._wells_priority[well1] > self._wells_priority[well2]:
                self.Add(self.well_start(well1) <= self.well_start(well2))
            elif self._wells_priority[well1] < self._wells_priority[well2]:
                self.Add(self.well_start(well1) >= self.well_start(well2))

    def _enforce_one_slot_assigned_to_well(self):
        """
        Adds a constraint enforcing an assignment of wells to slots, such that self.slot_used[slot][well]
        is true if the well is assigned to the slot.
        """
        for well in self.wells:
            self.Add(sum([self.slot_used[slot][well] for slot in self.slots]) == 1)

    def _enforce_slot_used_once(self):
        """
        Adds a constraint enforcing an assignment of wells to slots, such that self.slot_used[slot][well]
        is true if the well is assigned to the slot.
        """
        for slot in self.slots:
            self.Add(sum(self.slot_used[slot].values()) <= 1)


def evaluate(max_solver_time=3600, *args, **kwargs):
    model = WellDrillScheduleModel(*args, **kwargs)
    logger.debug(model.ModelStats())

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_solver_time
    logger.debug(
        "Solver set with maximum solve time of {} seconds".format(max_solver_time)
    )

    logger.info("Optimization solver starting..")
    status = solver.Solve(model)

    logger.debug("Solver completed with status: {}".format(status))
    msg = (
        "Detailed solver status: \n"
        "Number of conflicts: {}\n"
        "Objective Value: {}\n"
        "Walltime: {}\n"
    )
    logger.debug(
        msg.format(solver.NumConflicts(), solver.ObjectiveValue(), solver.WallTime())
    )

    schedule = []
    if status == cp_model.OPTIMAL:
        well_end_days = {
            well: solver.Value(model.well_end(well)) for well in model.wells
        }
        well_start_days = {
            well: solver.Value(model.well_start(well)) for well in model.wells
        }
        for (well, rig) in model.well_rig_pairs():
            task = model.task(well, rig)
            for slot in model.slots:
                valid_event = (
                    well_end_days[well] == solver.Value(task.end)
                    and solver.Value(model.slot_used[slot][well]) == 1
                )
                if valid_event:
                    schedule_event = ScheduleType(
                        rig=rig,
                        slot=slot,
                        well=well,
                        start_date=model.start_date
                        + datetime.timedelta(days=well_start_days[well]),
                        end_date=model.start_date
                        + datetime.timedelta(days=well_end_days[well]),
                    )
                    schedule.append(schedule_event)
    return schedule
