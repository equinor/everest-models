#!/usr/bin/env python

import logging
import typing
from functools import partial

from spinningjenny.jobs.fm_well_constraints.models import Constraints
from spinningjenny.jobs.fm_well_constraints.parser import build_argument_parser
from spinningjenny.jobs.fm_well_constraints.tasks import create_well_operations

logger = logging.getLogger(__name__)


def _collect_constraints_errors(
    optional_constraints: typing.Iterable[typing.Tuple[Constraints, str]],
    well_names: typing.Iterable[str],
):
    for argument, constraint in optional_constraints:
        constraint = set() if constraint is None else set(dict(constraint))
        if diff := constraint.difference(well_names):
            yield f"\t{argument}_constraints:\n\t\t{'    '.join(diff)}"


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)

    mismatch_errors = []

    constraints = tuple(
        filter(
            lambda x: x[1],
            (
                ("rate", options.rate_constraints),
                ("duration", options.duration_constraints),
                ("phase", options.phase_constraints),
            ),
        )
    )

    if errors := list(
        _collect_constraints_errors(
            constraints,
            well_names=[well.name for well in options.input],
        )
    ):
        mismatch_errors.append(
            "Constraint well name keys do not match input well names:\n"
            + "\n".join(errors)
        )

    if errors := set(options.config.keys()).difference(
        well.name for well in options.input if well.readydate is not None
    ):
        mismatch_errors.append(
            "Missing start date (keyword: readydate) for the following wells:\n\t"
            + "\t".join(errors)
        )

    if mismatch_errors:
        args_parser.error("\n\n".join(mismatch_errors))

    if options.lint:
        args_parser.exit()

    operations = partial(create_well_operations, constraints=dict(constraints))
    for well in options.input:
        well.ops = (
            *well.ops,
            *operations(options.config.get(well.name, {}), well.name, well.readydate),
        )

    options.input.json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
