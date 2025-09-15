from everest_models.jobs.fm_drill_planner.manager import get_field_manager
from everest_models.jobs.fm_drill_planner.parser import build_argument_parser
from everest_models.jobs.fm_drill_planner.tasks import orcastrate_drill_schedule

FULL_JOB_NAME = "Drill planner"

EXAMPLES = """

Argument examples
-----------------
:code:`-input` example

.. code-block:: JSON

        [
            {
                "name": "w1",
                "drill_time": 20
            },
            {
                "name": "w2",
                "drill_time": 25
            },
            {
                "name": "w3",
                "drill_time": 43
            },
            {
                "name": "w4",
                "drill_time": 23
            },
            {
                "name": "w5",
                "drill_time": 36
            }
        ]

:code:`-config` example

.. code-block:: yaml

        start_date: 2000-01-01
        end_date: 2001-01-01
        rigs:
         -
            name: 'A'
            wells: ['w1', 'w2', 'w3']
            slots: ['S1', 'S2', 'S3']
            unavailability:
             -
                start: 2000-01-01
                stop: 2000-02-02
             -
                start: 2000-03-14
                stop: 2000-03-19
         -
            name: 'B'
            wells: ['w3', 'w4', 'w5']
            slots: ['S3', 'S4', 'S5']
            unavailability:
             -
                start: 2000-02-01
                stop: 2000-02-02
             -
                start: 2000-02-14
                stop: 2000-02-15
        slots:
         -
            name: 'S1'
            wells: ['w1', 'w2', 'w3']
            unavailability:
             -
                start: 2000-02-01
                stop: 2000-02-03
         -
            name: 'S2'
            wells: ['w1', 'w2', 'w3']
         -
            name: 'S3'
            wells: ['w1', 'w2', 'w3']
         -
            name: 'S4'
            wells: ['w3', 'w4', 'w5']
         -
            name: 'S5'
            wells: ['w3', 'w4', 'w5']


:code:`-optimizer` example

.. code-block:: yaml

        w1: 5
        w2: 4
        w3: 3
        w4: 2
        w5: 1


"""


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)

    if options.input and options.config.wells:
        args_parser.error("--input and config.wells are mutually exclusive!")

    if not options.input and not options.config.wells:
        args_parser.error("either --input or config.wells must be provided!")

    wells_input = options.input or options.config.wells
    well_dict = wells_input.to_dict()

    manager = get_field_manager(
        options.config,
        wells_input,
        options.optimizer,
        options.ignore_end_date,
        options.lint,
    )

    if options.lint:
        args_parser.exit()
    orcastrate_drill_schedule(
        manager, well_dict, options.config.start_date, options.time_limit
    )
    wells_input.json_dump(options.output)
