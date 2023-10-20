import bisect
import datetime
import logging
import pathlib
import re
from typing import Any, Dict, List, Union

from jinja2 import Template

from everest_models.jobs.shared.models import PhaseEnum

logger = logging.getLogger(__name__)

OperationParameter = Dict[str, Union[pathlib.Path, PhaseEnum, float, str]]
OperationData = Dict[datetime.datetime, List[OperationParameter]]
MODIFY_COMMENT = "-- MODIFIED by schmerge forward model\n"
ECLIPSE_DATE_REGEX = re.compile(
    r"^DATES.*?"  # starting from `DATE` tag
    r"\n\s?(?<!--)\s?"  # insure not a commented out date
    r"(?P<date>\d{1,2}\s+\S+\s+\d{4})"  # Capture the date
    r".*?/.*?/.*?\n"  # end of line markers
    r"(?P<comments>.*?)"  # Capture everything (comment) between dates
    r"(?=DATES)",  # Till the next date (none capturing group)
    re.VERBOSE | re.MULTILINE | re.DOTALL,
)


def _render_parameter_data(
    date: datetime.date, template: pathlib.Path, template_map: Dict[str, Any]
):
    if phase := template_map.pop("phase", None):
        template_map["phase"] = phase.value

    logger.info(
        f"Inserting {template} with params {template_map} at {date.strftime('%d %b %Y').upper()}"
    )
    return (
        f"--start {template}\n\n"
        f"{Template(template.read_text()).render(**template_map)}\n\n"
        f"--end {template}\n\n"
    )


def _format_insertion_date(date: datetime.date) -> str:
    return f"\n\nDATES\n {date.strftime('%d %b %Y').upper()} / --ADDED\n/\n\n"


def _find_dates_in_schedule(source: str):
    return {
        datetime.datetime.strptime(
            re.sub(
                r"['\"]",  # Drop quotation
                "",
                date.replace("JLY", "JUL")  # Replace JLY
                if "JLY" in (date := match["date"])  # date group
                else date,
            ),
            "%d %b %Y",
        ).date(): match[
            0
        ]  # Convert to date
        for match in ECLIPSE_DATE_REGEX.finditer(f"{source}DATES")
    }


def _merge_operations_onto_schedule(operations: OperationData, schedule: str) -> str:
    if re.search(r"(?<=\n)(DATES)", schedule) is None:
        return schedule + "".join(
            _format_insertion_date(date)
            + "".join(
                _render_parameter_data(date, **parameters) for parameters in entry
            )
            for date, entry in sorted(operations.items())
        )
    schedule_data = _find_dates_in_schedule(schedule)
    dates = tuple(schedule_data)
    # Walk through parsed schedule in reverse in order to preserve data
    for operation_date, entry in reversed(sorted(operations.items())):
        if operation_date in dates:
            closest_date = operation_date
            insertion_text = "\n\n"
        else:
            closest_date = dates[
                date - 1
                if (date := bisect.bisect_left(dates, operation_date))
                else date
            ]
            insertion_text = _format_insertion_date(operation_date)
        insertion_text = insertion_text + "\n\n".join(
            _render_parameter_data(operation_date, **parameters) for parameters in entry
        )
        schedule = re.sub(
            f"({schedule_data[closest_date]})",
            (r"\1" + insertion_text)
            if closest_date <= operation_date  # is operation date before closest date ?
            else (insertion_text + r"\1"),
            schedule,
        )
    return schedule


def merge_operations_onto_schedule(operations: OperationData, schedule: str) -> str:
    """Merge well operation onto given schedule.

    - render well operation template and parameters
    - Inject rendered string onto schedule under the correct date
    - Add date if not present in schedule

    Args:
        operations (OperationData): <date, operation> mapping
        schedule (str): eclipse schedule

    Returns:
        str: schedule
    """
    schedule = re.sub(
        r"(?<=\n)(DATES)",
        f"\n{MODIFY_COMMENT}\n" + r"\1",  # insert modification comment
        _merge_operations_onto_schedule(operations, schedule),
        count=1,
    )
    return re.sub(r"\n{3,}", "\n\n", schedule)  # uniform format
