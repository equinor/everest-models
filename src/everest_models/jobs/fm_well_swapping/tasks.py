from argparse import Namespace
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import accumulate, takewhile
from pathlib import Path
from typing import (
    Any,
    DefaultDict,
    Dict,
    Iterable,
    Iterator,
    List,
    Sequence,
    Tuple,
    TypeVar,
)

from everest_models.jobs.shared.models import Operation
from everest_models.jobs.shared.models import Well as CaseConfig
from everest_models.jobs.shared.models import Wells as CasesConifg

from .models import Case, Quota, State
from .state_processor import StateProcessor

T = TypeVar("T", tuple, list)


def _limit_iterations(value: T, limit: int) -> T:
    return value[:limit] if limit else value


@dataclass
class Data:
    """
    Attributes:
        lint_only: A boolean flag indicating if only linting is required.
        iterations: The limit on the number of iterations.
        priorities: The sorted case of priorities per iteration.
        quotas: A dictionary of quotas per iteration for each state.
        initial_states: Each case's states at iteration zero.
        cases: The list of cases to be processed.
        output: The output location.
        targets: The list of target states per iterations.
        state_duration: The state duration constraints.
    """

    lint_only: bool
    iterations: int
    priorities: Tuple[Tuple[Case, ...], ...]
    quotas: Dict[State, List[Quota]]
    initial_states: Dict[Case, State]
    cases: CasesConifg
    output: Path
    targets: Tuple[State, ...]
    state_duration: Tuple[int, ...]
    errors: List[str]


def clean_parsed_data(options: Namespace) -> Data:
    """Cleans and validates command line options.

    Args:
        options (Namespace): The parsed command line options.

    Returns:
        A Data object containing cleaned and validated data.

    This function takes the parsed command line options and performs various validations and cleaning operations on the data.
    It checks if the command is 'lint' and sets a flag accordingly. It then validates and sorts the priorities, sets a limit based on the iteration limit or the length of priorities, and creates a Data object with the cleaned and validated data.
    Any errors encountered during the cleaning and validation process are stored in the 'errors' list.

    Typical usage example:
        options = parse_command_line_arguments()
        cleaned_data = clean_parsed_data(options)
    """

    errors: List[str] = []
    lint_only = options.command == "lint"

    def validate_exist(value: Any, message: str, skip_on_lint: bool = False):
        if not (value or skip_on_lint) and lint_only:
            errors.append(message)
        return value

    priorities = validate_exist(
        sorted_case_priorities(
            options.priorities or options.config.priorities.inverted
            if options.config.priorities
            else []
        ),
        "no priorities",
    )

    limit = (
        len(priorities)
        if not options.iteration_limit or options.iteration_limit > len(priorities)
        else options.iteration_limit
    )

    return Data(
        lint_only,
        iterations=limit,
        priorities=_limit_iterations(priorities, limit),
        quotas=validate_exist(
            {
                state.label: state.get_quotas(
                    limit, len(priorities[0]) if priorities else 0, errors
                )
                for state in options.config.state.hierarchy
            },
            "no states",
        ),
        initial_states=validate_exist(
            options.config.initial_states(priorities[0] if priorities else (), errors),
            "no initial states",
        ),
        cases=validate_exist(options.cases or options.config.cases(), "no cases"),
        output=validate_exist(options.output, "no output", skip_on_lint=True),
        targets=validate_exist(
            options.config.state.get_targets(limit, errors), "no targets"
        ),
        state_duration=_limit_iterations(
            validate_exist(
                options.config.constraints.rescale(
                    options.constraints["state_duration"]
                    if options.constraints
                    else limit
                ),
                "no state duration",
            ),
            limit,
        ),
        errors=errors,
    )


def sorted_case_priorities(
    values: List[Dict[str, float]],
) -> Tuple[Tuple[str, ...], ...]:
    return tuple(tuple(sorted(index, key=index.get, reverse=True)) for index in values)  # type: ignore


def inject_case_operations(
    cases: Dict[str, CaseConfig],
    params: Iterable[Tuple[date, Iterable[Tuple[Case, State]]]],
) -> None:
    """Injects case operations into the provided cases based on the given parameters.

    Args:
        cases (Dict[str, CaseConfig]): A dictionary mapping case names to Case objects.
        params (Iterable[Tuple[date, Iterator[Tuple[str, str]]]): A nested Iterable in the form of (date, ((case, state), ...)), ...

    Raises:
        KeyError: If a case name provided in the params does not exist in the cases dictionary.
        ValueError: If the date or operation state provided in the params is invalid.

    This function iterates through the provided params and injects the corresponding
    operations into the respective case. Each operation is validated using the
    Operation model before being added to the case's operations list.
    """
    cases_: DefaultDict[str, List[Operation]] = defaultdict(list)
    for _date, states in params:
        for case, state in states:
            if case not in cases:
                raise KeyError(f"Case '{case}' not found in case dictionary.")
            try:
                operation = Operation.model_validate({"date": _date, "opname": state})
            except ValueError as e:
                raise ValueError(
                    f"Invalid operation data: {_date}, {state}. {str(e)}"
                ) from e
            cases_[case].append(operation)

    for case, operation in cases_.items():
        cases[case].operations = (*cases[case].operations, *operation)  # type: ignore


def duration_to_dates(durations: Sequence[int], start_date: date) -> Iterator[date]:
    """Calculate a series of dates based on a list of time durations in days and a start date.

    Args:
        durations (Sequence[int]): time durations per index in days.
        start_date (date): The starting date from which to calculate the subsequent dates.

    Returns:
        (start date, date,..., nth date)
    """
    return (
        start_date + timedelta(days=duration)
        for duration in accumulate(durations, initial=0)
    )


def determine_index_states(
    process_params: Iterable[Tuple[Tuple[Case, ...], State]],
    state_processor: StateProcessor,
    iterations: int,
) -> Iterator[Iterator[Tuple[Case, State]]]:
    """Determine the states of cases at each index based on the process parameters.

    Args:
        process_params (Iterable[Tuple[Tuple[str, ...], str]]): A collection of tuples where each tuple contains a tuple of cases and a target state.
        state_processor (StateProcessor): An object that processes the cases and updates the states.
        iterations (int): The number of iterations to run the state processing for.

    Returns:
        An iterator of iterators where each inner iterator contains tuples of cases and their corresponding states.
    """
    return (
        state_processor.process(cases, target, index)
        for index, (cases, target) in takewhile(
            lambda x: x[0] < iterations, enumerate(process_params)
        )
    )
