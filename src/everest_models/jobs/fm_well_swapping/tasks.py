from datetime import date, timedelta
from itertools import accumulate
from typing import Dict, Iterable, Iterator, List, Sequence, Tuple

from .models import Operation, Well
from .state_processor import StateProcessor


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
            wells[well].operations.append(operation)


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
    Iterate through state paramenteres (wells, n_max_wells, n_switch_states) and process the well states for each index.

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
