import logging

from everest_models.jobs.fm_well_filter.parser import build_argument_parser

logger = logging.getLogger(__name__)

FULL_JOB_NAME = "Well filter"

EXAMPLES = """
Argument examples
~~~~~~~~~~~~~~~~~
:code:`-input` example

.. code-block:: json

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

:code:`-keep` example

.. code-block:: json

    ["w1", "w3", "w5"]

"""


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    keep = options.remove is None
    well_names = set(options.remove or options.keep)

    if diff := well_names.difference(well.name for well in options.input):
        logger.warning(
            f"{'Keep' if keep else 'Remove'} value(s) are not present in input file:\n\t"
            + ", ".join(diff)
        )

    if options.lint:
        args_parser.exit()

    options.input.root = tuple(
        filter(
            lambda x: x.name in well_names if keep else x.name not in well_names,
            options.input,
        )
    )

    options.input.json_dump(options.output)
