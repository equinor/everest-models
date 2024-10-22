from typing import Optional, Sequence

from .tasks import (
    clean_parsed_data,
    determine_index_states,
    duration_to_dates,
    inject_case_operations,
)

FULL_JOB_NAME = "Well swapping"


def main_entry_point(args: Optional[Sequence[str]] = None):
    data = clean_parsed_data(args)
    inject_case_operations(
        data.cases.to_dict(),
        zip(
            duration_to_dates(data.state_duration, data.start_date),
            determine_index_states(data.state, data.iterations, data.priorities),
        ),
    )
    data.cases.json_dump(data.output)
