#!/usr/bin/env python

import logging
from argparse import Namespace
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from .models import validate_priorities_and_state_initial_same_wells
from .parser import build_argument_parser
from .state_processor import StateProcessor
from .tasks import (
    determine_index_states,
    duration_to_dates,
    inject_well_operations,
    sorted_well_priorities,
)

logger = logging.getLogger(__name__)


class Data(NamedTuple):
    priorities: Tuple[Tuple[str, ...], ...]
    initial_states: Dict[str, str]
    n_max_wells: Tuple[int, ...]
    n_switch_states: Tuple[int, ...]
    state_duration: Tuple[int, ...]
    errors: List[str]


def clean_incoming_data(options: Namespace) -> Data:
    errors: List[str] = []
    if not (
        priorities := sorted_well_priorities(
            options.priorities or options.config.index_priorities
        )
    ):
        errors.append("no priorities")
    try:
        validate_priorities_and_state_initial_same_wells(
            set(priorities[0]), set(options.config.state.wells)
        )
    except ValueError as e:
        errors.append(str(e))

    if not (
        constraints := options.config.rescale_constraints(options.constraints)
        if options.constraints
        else options.config.constraints
    ):
        errors.append("no constraints")

    return Data(
        priorities,
        options.config.initial_states(priorities[0]),
        **constraints,
        errors=errors,
    )


def main_entry_point(args: Optional[Sequence[str]] = None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    data = clean_incoming_data(options)
    if data.errors:
        args_parser.error("\n".join(data.errors))

    if args and args[0] == "parse":
        args_parser.exit()

    inject_well_operations(
        options.input.to_dict(),
        zip(
            duration_to_dates(
                data.state_duration,
                options.config.start_date,
            ),
            determine_index_states(
                zip(data.priorities, data.n_max_wells, data.n_switch_states),
                StateProcessor(
                    default=options.config.state.viable[0],
                    is_allow_action=options.config.state.is_allow_action,
                    latest=data.initial_states,
                    actions=None
                    if options.allow_reopen
                    else options.config.state.actions,
                ),
            ),
        ),
    )
    options.input.json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
