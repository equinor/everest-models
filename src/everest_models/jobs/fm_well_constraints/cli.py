#!/usr/bin/env python

import logging
import typing
from functools import partial

from .models import WellConstraints
from .parser import build_argument_parser
from .tasks import constraint_by_well_name, create_well_operations

logger = logging.getLogger(__name__)


def _collect_constraints_errors(
    optional_constraints: WellConstraints,
    well_names: typing.Iterable[str],
):
    errors = []
    for argument, constraint in optional_constraints.items():
        constraint = set() if constraint is None else set(constraint)  # type: ignore
        if diff := constraint.difference(well_names):
            errors.append(f"\t{argument}_constraints:\n\t\t{'    '.join(diff)}")
    return errors


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)

    mismatch_errors = []

    constraints = WellConstraints(
        duration=options.duration_constraints,
        rate=options.rate_constraints,
        phase=options.phase_constraints,
    )
    if errors := _collect_constraints_errors(
        constraints,
        well_names=[well.name for well in options.input],
    ):
        mismatch_errors.append(
            "Constraint well name keys do not match input well names:\n"
            + "\n".join(errors)
        )

    if errors := set(options.config).difference(
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
    _well_constraints = partial(constraint_by_well_name, constraints=constraints)
    for well in options.input:
        well.operations = (
            *well.operations,
            *create_well_operations(
                options.config.get(well.name, {}),
                well.readydate,
                _well_constraints(well_name=well.name),
            ),
        )

    options.input.json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
