import functools
import itertools
import logging
from typing import Dict, Iterable, List

from everest_models.jobs.fm_drill_planner.data import Event, Rig, Slot, WellPriority
from everest_models.jobs.fm_drill_planner.data.validators import event_failed_conditions
from everest_models.jobs.fm_drill_planner.planner import (
    drill_constraint_model,
    get_greedy_drill_plan,
    run_optimization,
)

logger = logging.getLogger(__name__)


def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class ScheduleError(Exception): ...


class FieldManager:
    def __init__(
        self,
        wells: Dict[str, WellPriority],
        slots: Dict[str, Slot],
        rigs: Dict[str, Rig],
        horizon: int,
    ) -> None:
        self._wells = wells
        self._slots = slots
        self._rigs = rigs
        self._horizon = horizon
        self._greedy_schedule = get_greedy_drill_plan(wells, slots, rigs, horizon)
        self._optimize_schedule = []

    def schedule(self) -> List[Event]:
        schedule = self._schedule()
        if failed_condition := "\t".join(
            event_failed_conditions(
                schedule, self._wells, self._slots, self._rigs, self._horizon
            )
        ):
            raise ScheduleError(
                f"Schedule is not valid, failed on the following conditions:\n\t{failed_condition}"
            )
        return self._resolve_schedule_priorities(schedule)

    def _resolve_schedule_priorities(self, schedule: Iterable[Event]) -> List[Event]:
        """
        The priorities are not hard constraints in the solvers, which they shouldn't be.
        Both implementations should prioritize the higher priority wells first.
        If, and only if, higher priority wells are not affected, a lower priority well
        can be drilled first. Otherwise forcing the startup for lower priority wells
        could result in wells not being drilled.

        The output of the entire job however should not allow for ready_dates to be
        in any other order than as a prioritized list. We therefore shift any
        dates that are not in order.
        """

        def priority(previous, current):
            if previous.end > current.end:
                current.end = previous.end
                logger.info(
                    f"Well {current.well} could be completed prior to well {previous.well}, "
                    f"without affecting {previous.well}. End date for {current.well} shifted "
                    "to conform with priority"
                )
            return current

        sorted_schedule = sorted(
            schedule, key=lambda x: self._wells[x.well].priority, reverse=True
        )

        return [
            sorted_schedule[0],
            *[priority(prev, curr) for prev, curr in pairwise(sorted_schedule)],
        ]

    def _schedule(self) -> List[Event]:
        if self._greedy_schedule and self._optimize_schedule:
            return self._compare_schedules()
        return self._greedy_schedule

    def _compare_schedules(self):
        if len(self._optimize_schedule) != len(self._greedy_schedule):
            return max([self._optimize_schedule, self._greedy_schedule])
        sorted_events = functools.partial(
            sorted, key=lambda event: self._wells[event.well].priority, reverse=True
        )
        return next(
            (
                self._optimize_schedule
                if optimized_event.end < greedy_event.end
                else self._greedy_schedule
                for optimized_event, greedy_event in zip(
                    sorted_events(self._optimize_schedule),
                    sorted_events(self._greedy_schedule),
                )
            ),
            self._optimize_schedule,
        )

    def run_schedule_optimization(self, time_limit) -> None:
        if not any(rig.delay for rig in self._rigs.values()):
            self._optimize_schedule = run_optimization(
                drill_constraint_model(
                    self._wells,
                    self._slots,
                    self._rigs,
                    self._horizon,
                    best_guess_schedule=self._greedy_schedule,
                ),
                max_time_seconds=time_limit,
            )
