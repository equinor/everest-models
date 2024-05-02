from argparse import Namespace
from collections import defaultdict
from datetime import date, timedelta
from itertools import accumulate
from pathlib import Path
from typing import (
    Any,
    DefaultDict,
    Dict,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    Sequence,
    Tuple,
)

from everest_models.jobs.shared.models import Operation, Well, Wells

from .model_config import validate_priorities_and_state_initial_same_wells
from .state_processor import StateProcessor


class Data(NamedTuple):
    lint_only: bool
    priorities: Tuple[Tuple[str, ...], ...]
    initial_states: Dict[str, str]
    wells: Wells
    output: Path
    n_max_wells: Tuple[int, ...]
    n_switch_states: Tuple[int, ...]
    state_duration: Tuple[int, ...]
    errors: List[str]


def clean_parsed_data(options: Namespace) -> Data:
    """
    Cleans command-line parsed data and returns a Data object.

    if errors are trigger it will be written to Data.errors

    Parameters:
    options (Namespace): A command-line parsed options

    Returns:
    Data: (cleaned data and/or errors).
      - lint_only
      - priorities
      - initial_states
      - wells
      - output
      - n_max_wells
      - n_switch_states
      - state_duration
      - errors
    """

    errors: List[str] = []
    lint_only = options.command == "lint"

    def validate_exist(value: Any, message: str):
        if not (value or lint_only):
            errors.append(message)
        return value

    priorities = validate_exist(
        sorted_well_priorities(
            options.priorities or options.config.priorities.inverted
        ),
        "no priorities",
    )

    try:
        validate_priorities_and_state_initial_same_wells(
            set(priorities[0]), set(options.config.state.wells)
        )
    except ValueError as e:
        errors.append(str(e))

    return Data(
        lint_only,
        priorities,
        options.config.initial_states(priorities[0]),
        wells=validate_exist(
            options.wells or options.config.wells_instance(), "no wells"
        ),
        output=validate_exist(options.output or options.config.output, "no output"),
        **validate_exist(
            options.config.constraints.rescale(options.constraints), "no constraints"
        ),
        errors=errors,
    )


def sorted_well_priorities(
    values: List[Dict[str, float]],
) -> Tuple[Tuple[str, ...], ...]:
    return tuple(tuple(sorted(index, key=index.get, reverse=True)) for index in values)  # type: ignore


def inject_well_operations(
    wells: Dict[str, Well], params: Iterable[Tuple[date, Iterable[Tuple[str, str]]]]
) -> None:
    """
    Injects well operations into the provided wells based on the given parameters.

    Parameters:
    - wells (Dict[str, Well]): A dictionary mapping well names to Well objects.
    - params (Iterable[Tuple[date, Iterator[Tuple[str, str]]]): A nested Iterable in the form of (date, ((well, state), ...)), ...

    Returns:
    - None

    Raises:
    - KeyError: If a well name provided in the params does not exist in the wells dictionary.
    - ValueError: If the date or operation state provided in the params is invalid.

    This function iterates through the provided params and injects the corresponding operations into the respective wells.
    Each operation is validated using the Operation model before being added to the well's operations list.
    """
    wells_: DefaultDict[str, List[Operation]] = defaultdict(list)
    for _date, states in params:
        for well, state in states:
            if well not in wells:
                raise KeyError(f"Well '{well}' not found in wells dictionary.")
            try:
                operation = Operation.model_validate({"date": _date, "opname": state})
            except ValueError as e:
                raise ValueError(
                    f"Invalid operation data: {_date}, {state}. {str(e)}"
                ) from e
            wells_[well].append(operation)

    for well, operation in wells_.items():
        wells[well].operations = (*wells[well].operations, *operation)  # type: ignore


def duration_to_dates(durations: Sequence[int], start_date: date) -> Iterator[date]:
    """
    Calculate a series of dates based on a list of time durations in days and a start date.

    Args:
    durations (Sequence[int]): time durations per index in days.
    start_date (date): The starting date from which to calculate the subsequent dates.

    Returns:
    Iterator[date, ...]: (start date, date,..., nth date)
    """
    return (
        start_date + timedelta(days=duration)
        for duration in accumulate(durations, initial=0)
    )


def determine_index_states(
    process_params: Iterable[Tuple[Tuple[str, ...], int, int]],
    state_processor: StateProcessor,
) -> Iterator[Iterator[Tuple[str, str]]]:
    """
    Iterate through state parameters (wells, n_max_wells, n_switch_states) and process the well states for each index.

    Args:
        process_params(Iterable[Tuple[Tuple[str, ...], int, int]],):
            - well order from highest to lowest priority
            - maximum number of wells to processed
            - numeber of switch states allowed
        state_processor (StateProcessor): state processor to run per index

    Returns:
    Iterator[Iterator[Tuple[str, str]]]: ((well, states),...) per index
    """
    return (
        state_processor.process(wells, n_max_wells, n_switch_states)
        for wells, n_max_wells, n_switch_states in process_params
    )
