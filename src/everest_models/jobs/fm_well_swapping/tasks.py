from argparse import Namespace
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import accumulate, chain
from logging import getLogger
from pathlib import Path
from typing import (
    Any,
    DefaultDict,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

from everest_models.jobs.fm_well_swapping.models.state import StateConfig
from everest_models.jobs.fm_well_swapping.parser import build_argument_parser
from everest_models.jobs.shared.models import Operation
from everest_models.jobs.shared.models import Well as CaseConfig
from everest_models.jobs.shared.models import Wells as CasesConifg

from .models import Case, State
from .state_processor import StateProcessor

T = TypeVar("T", tuple, list)
logger = getLogger("Well Swapping")


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
    start_date: date
    iterations: int
    priorities: Tuple[Tuple[Case, ...], ...]
    state: StateConfig
    cases: CasesConifg
    output: Optional[Path]
    state_duration: Tuple[float, ...]
    errors: List[str]


def clean_data(options: Namespace) -> Data:
    """Cleans command line options.

    Args:
        options (Namespace): The parsed command line options.

    Returns:
        A Data object containing cleaned and validated data.

    This function takes the parsed command line options and performs various validations
    and cleaning operations on the data. It checks if the command is 'lint' and sets a
    flag accordingly. It then validates and sorts the priorities, sets a limit based on
    the iteration limit or the length of priorities, and creates a Data object with the
    cleaned and validated data. Any errors encountered during the cleaning and validation
    process are stored in the 'errors' list.

    Typical usage example:
        options = parse_command_line_arguments()
        cleaned_data = clean_data(options)
    """
    errors: List[str] = []

    def validate_exist(value: Any, argument: str):
        if not (value or options.lint) and hasattr(options, argument):
            errors.append(f"no {' '.join(argument.split('_'))}")
        return value

    priorities = validate_exist(
        sorted_case_priorities(
            options.priorities
            if options.priorities
            else options.config.priorities.inverted
            if options.config.priorities
            else []
        ),
        "priorities",
    )
    iteration_capacity = len(priorities)
    iteration_limit = (
        options.iteration_limit
        if 0 < options.iteration_limit < iteration_capacity
        else iteration_capacity
    )

    if options.constraints and "state_duration" in options.constraints:
        state_duration = options.constraints["state_duration"]
    elif isinstance(options.config.constraints.state_duration.fallback_values, float):
        state_duration = (
            options.config.constraints.state_duration.fallback_values,
        ) * iteration_capacity
    else:
        state_duration = options.config.constraints.state_duration.fallback_values

    return Data(
        options.lint,
        start_date=options.config.start_date,
        iterations=iteration_limit,
        priorities=priorities,
        state=options.config.state,
        cases=validate_exist(options.cases or options.config.cases(), "cases"),
        output=None if options.lint else validate_exist(options.output, "output"),
        state_duration=validate_exist(state_duration, "state_duration"),
        errors=errors,
    )


def clean_parsed_data(
    args: Optional[Sequence[str]] = None, hook_call: bool = False
) -> Data:
    parser = build_argument_parser()
    options = parser.parse_args(args)
    data = clean_data(options)

    if hook_call:
        return data

    if data.errors:
        erros = "\n".join(data.errors)
        logger.error(erros)
        parser.error(erros)

    if options.lint:
        parser.exit()
    return data


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
        params (Iterable[Tuple[date, Iterator[Tuple[str, str]]]): A nested Iterable in
        the form of (date, ((case, state), ...)), ...

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
    state: StateConfig, limit: int, priorities: Iterable[Tuple[Case, ...]]
) -> Iterator[Iterator[Tuple[Case, State]]]:
    case_names = tuple(set(chain.from_iterable(priorities)))
    processor = StateProcessor.from_state_config(state, case_names)
    for index, (cases, target, quotas) in enumerate(
        zip(
            priorities,
            state.get_targets(limit),
            state.get_quotas(limit, len(case_names)),
            strict=False,
        )
    ):
        if not processor.is_locked:
            processor.process(cases, target, quotas)
            yield processor.latest_valid_states(index)
        else:
            yield processor.latest_valid_states(max(index - 1, 0))
            break
