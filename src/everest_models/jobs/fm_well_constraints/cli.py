import logging
import typing
from functools import partial

from .models import WellConstraints
from .parser import build_argument_parser
from .tasks import constraint_by_well_name, create_well_operations

logger = logging.getLogger(__name__)

FULL_JOB_NAME = "Well constraints"

EXAMPLES = """
Argument examples
~~~~~~~~~~~~~~~~~

If there is an entry in e.g. the rate-constraint file for `INJECT1`, `1`, then
no rate value needs to be provided in the configuration file under index `1` for `INJECT1`.
The optimizer values from the rate-constraint and duration-constraint files will overwrite
any value provided in the configuration file for the same well and index.
If the optimizer provides no rate or duration input files then any values in the configuration files
will be considered as constants.


:code:`-phase-constraint` example

.. code-block:: json

    {
    "INJECT1" : {
      "1": 0.49,
      "2": 0.51,
      "3": 0.8
    },
    "INJECT2" : {
      "1": 0.3,
      "2": 0.1
    }}

:code:`-config` example

.. code-block:: yaml

    INJECT1:
        1:
          phase:
            options: [water, gas]
        2:
          phase:
            options: [water, gas]
        3:
          phase:
            options: [water, gas]

    INJECT2:
        1:
          phase:
            options: [water, gas]
        2:
          phase:
            options: [water, gas]


:code:`-rate-constraint` example

.. code-block:: json

    {
    "INJECT1" : {
      "1": 600,
      "2": 400,
      "3": 200
    },
    "INJECT2" : {
      "1": 650,
      "2": 525
    }}

:code:`-config` example

.. code-block:: yaml

    INJECT1:
        1:
          phase:
            value: WATER
          duration:
            value 30
        2:
          phase:
            value: WATER
          duration:
            value 40
        3:
          phase:
            value: GAS
          duration:
            value: 70
        4:
          phase:
            value: GAS
          rate:
            value: 333 # Will be considered a constat rate
          duration:
            value: 100

    INJECT2:
        1:
          phase:
            value: WATER
          duration:
            value: 50
        2:
          phase:
            value: GAS
          duration:
            value: 60

:code:`-duration-constraint` example

.. code-block:: json

    {
    "INJECT1" : {
      "1": 60,
      "2": 40,
    }}

:code:`-config` example

.. code-block:: yaml

    INJECT1:
        1:
          phase:
            value: WATER
        2:
          phase:
            value: WATER
        3:
          phase:
            value: GAS
          duration:
            value: 70


:code:`-input` example

.. code-block:: json

    [
      {
        "name": "INJECT1",
        "readydate": "2019-05-12",
        "ops": [
            {"opname": "open", "date": "2019-05-12"}
        ]
      },
      {
        "name": "INJECT2",
        "readydate": "2019-09-15",
        "ops": [
            {"opname": "open", "date": "2019-09-15"}
        ]
      }
    ]

"""


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
