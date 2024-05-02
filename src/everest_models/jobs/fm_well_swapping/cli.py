#!/usr/bin/env python

import logging
from typing import Optional, Sequence

from .parser import build_argument_parser
from .state_processor import StateProcessor
from .tasks import (
    clean_parsed_data,
    determine_index_states,
    duration_to_dates,
    inject_well_operations,
)

logger = logging.getLogger(__name__)


def main_entry_point(args: Optional[Sequence[str]] = None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    data = clean_parsed_data(options)
    if data.errors:
        args_parser.error("\n".join(data.errors))

    if data.lint_only:
        args_parser.exit()

    inject_well_operations(
        data.wells.to_dict(),
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
    data.wells.json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
