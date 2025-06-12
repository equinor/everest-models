from typing import Optional, Sequence

from .tasks import (
    clean_parsed_data,
    determine_index_states,
    duration_to_dates,
    inject_case_operations,
)

FULL_JOB_NAME = "Well swapping"

EXAMPLES = """
Argument examples
~~~~~~~~~~~~~~~~~

Example of a well swapping configuration file (:code:`-c, --config`) for a case with 4 wells, 3 time intervals and 3 possible statuses:

.. code-block:: yaml

    start_date: 2025-01-01

    state:
        hierarchy:
            - label: open
              quotas: 3
            - label: closed
              quotas: [1, 1, 0, _]
            - label: shut
        initial:
            WELL-1: open
            WELL-2: closed
            WELL-3: closed
            WELL-4: open
        targets: [open, open, open]
        actions:
            - [open, closed]
            - [closed, open]
            - [open, shut]
            - [closed, shut]
        allow_inactions: true
        forbiden_actions: false

    case_file: ./wells.json

Example of swapping constraints controls for a case with 3 time intervals defined in :code:`controls` section of EVEREST configuration file:

.. code-block:: yaml

    controls:
        -
            name: swapping_constraints
            type: generic_control
            min: 0.0
            max: 500.0
            perturbation_magnitude: 25.0
            variables:
                - { name: state_duration, initial_guess: [250, 250, 250] }

These controls result in an EVEREST-generated JSON file with the following content (:code:`-cr, --constraints`):

.. code-block:: json

    {
        "state_duration": {
            "1": 250,
            "2": 250,
            "3": 250
        }
    }

Example of priority controls for a case with 4 wells and 3 time intervals defined in controls section of EVEREST configuration file:

.. code-block:: yaml

    -
        name: well_order
        type: well_control
        min: 0.0
        max: 1.0
        perturbation_magnitude: 0.05
        variables:
            - { name: WELL-1, initial_guess: [0.55, 0.51, 0.53] }
            - { name: WELL-2, initial_guess: [0.53, 0.55, 0.51] }
            - { name: WELL-3, initial_guess: [0.51, 0.53, 0.55] }
            - { name: WELL-4, initial_guess: [0.50, 0.50, 0.50] }

These controls result in an EVEREST-generated JSON file with the following content (:code:`-p, --priorities`):

.. code-block:: json

    {
        "WELL-1": {
            "1": 0.55,
            "2": 0.51,
            "3": 0.53
        },
        "WELL-2": {
            "1": 0.53,
            "2": 0.55,
            "3": 0.51
        },
        "WELL-3": {
            "1": 0.51,
            "2": 0.53,
            "3": 0.55
        },
        "WELL-4": {
            "1": 0.5,
            "2": 0.5,
            "3": 0.5
        }
    }

:code:`-cs, --cases` example for a case with 4 wells:

.. code-block:: json

    [
        {
            "name": "WELL-1"
        },
        {
            "name": "WELL-2"
        },
        {
            "name": "WELL-3"
        },
        {
            "name": "WELL-4"
        }
    ]

"""


def main_entry_point(args: Optional[Sequence[str]] = None):
    data = clean_parsed_data(args)
    inject_case_operations(
        data.cases.to_dict(),
        zip(
            duration_to_dates(data.state_duration, data.start_date),
            determine_index_states(data.state, data.iterations, data.priorities),
            strict=False,
        ),
    )
    data.cases.json_dump(data.output)
