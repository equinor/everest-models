import datetime
import logging
import pathlib
import re
from typing import Dict, Iterable, List, NamedTuple, Union

import sortedcontainers
from jinja2 import Template

from spinningjenny.jobs.shared.models import PhaseEnum, eclipse_dates

logger = logging.getLogger(__name__)

OperationParameter = Dict[str, Union[pathlib.Path, PhaseEnum, float, str]]
OperationData = Dict[datetime.datetime, List[OperationParameter]]
MODIFY_COMMENT = "-- MODIFIED by schmerge forward model\n"
SCHEDULE_HEADER = r"(\s*(?<=RPTRST)\s+(?:BASIC=)\d\s+(?:FREQ=)\d\s+/\s*(?:-- .*$)*\s*)"

__all__ = ["ScheduleInserter"]


def _date_pattern(date: datetime.date):
    return (
        r"(?P<date_snippet>(?<!\s--\s)DATES(?:[^/]*\n)+\s*0?"
        f"{date.day}"
        r"\s(?P<quote>['\"]?)"
        f"{date.strftime('%b').upper()}"
        r"(?P=quote)\s+"
        f"{date.year}"
        r"\s*/(?:[^/]*\s)+/"
        r"((?:[^/]*\n)+END(?:[^/]\n)*)?)"
    )


def _render_parameter_string(operation_parameters: Iterable[OperationParameter]):
    def render_parameter_data(
        template: pathlib.Path, phase: PhaseEnum = None, **kwargs
    ):
        if phase is not None:
            kwargs["phase"] = phase.value
        return (
            f"--start {template}\n\n"
            f"{Template(template.read_text()).render(**kwargs)}\n\n"
            f"--end {template}\n\n"
        )

    for parameters in operation_parameters:
        yield render_parameter_data(**parameters)
        logger.info(f"{parameters.pop('template')} with params {parameters} inserted")


def _clean_string(string: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", string)


class _Date(NamedTuple):
    date: datetime.date
    value: str
    for_insertion: bool = True


class ScheduleInserter:
    def __init__(self, schedule: str) -> None:
        self._schedule = schedule
        self._matches = sortedcontainers.SortedList(
            eclipse_dates(schedule), key=lambda x: x.date
        )

    def _re_sub(self, pattern: str, repl: str, **kwargs) -> None:
        self._schedule = re.sub(pattern, repl, self._schedule, **kwargs)

    def _apply_insertions(self) -> None:
        for index, match in enumerate(self._matches):
            if not match.for_insertion:
                continue
            self._re_sub(
                f"({self._matches[index - 1].value})"
                if index
                else f"({SCHEDULE_HEADER})",
                r"\1" + match.value,
            )

    def _insert_missing_dates(self, dates: Iterable[datetime.date]) -> bool:
        if not (
            missing_dates := set(dates).difference(
                match.date for match in self._matches
            )
        ):
            return False
        self._matches.update(
            _Date(
                date=date,
                value=f"\n\nDATES\n {date.strftime('%d %b %Y').upper()} / --ADDED\n/\n\n",
            )
            for date in missing_dates
        )
        self._apply_insertions()
        return True

    def _insert_operation_parameters(self, operation_parameters: OperationData) -> bool:
        if not any(operation_parameters.values()):
            return False
        for date, parameters in operation_parameters.items():
            self._re_sub(
                _date_pattern(date),
                r"\g<date_snippet>\n\n"
                + "\n".join(_render_parameter_string(parameters)),
            )
        return True

    def insert_operations(self, operations: OperationData) -> None:
        if self._insert_missing_dates(
            iter(operations)
        ) | self._insert_operation_parameters(operations):
            self._re_sub(
                SCHEDULE_HEADER,
                r"\1" + f"\n{MODIFY_COMMENT}\n",
                flags=re.MULTILINE,
            )

    @property
    def schedule(self) -> str:
        return _clean_string(self._schedule)
