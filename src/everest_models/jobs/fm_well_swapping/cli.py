#!/usr/bin/env python

from logging import getLogger
from typing import Optional, Sequence

from .parser import build_argument_parser
from .state_machine import StateMachine
from .state_processor import StateProcessor
from .tasks import (
    clean_parsed_data,
    determine_index_states,
    duration_to_dates,
    inject_case_operations,
)

logger = getLogger("Well Swapping")


def main_entry_point(args: Optional[Sequence[str]] = None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    data = clean_parsed_data(options)
    if data.errors:
        erros = "\n".join(data.errors)
        logger.error(erros)
        args_parser.error(erros)

    if data.lint_only:
        args_parser.exit()

    inject_case_operations(
        data.cases.to_dict(),
        zip(
            duration_to_dates(
                data.state_duration,
                options.config.start_date,
            ),
            determine_index_states(
                zip(data.priorities, data.targets),
                StateProcessor(
                    state_machine=StateMachine.from_config(options.config.state),
                    initial_states=data.initial_states,
                    quotas=data.quotas,
                ),
                iterations=data.iterations,
            ),
        ),
    )
    data.cases.json_dump(data.output)


if __name__ == "__main__":
    main_entry_point()
