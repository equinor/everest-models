#!/usr/bin/env python

import logging

import stea

from everest_models.jobs.fm_stea.parser import args_parser

logger = logging.getLogger(__name__)

FULL_JOB_NAME = "STEA"

EXAMPLES = """

Argument examples
~~~~~~~~~~~~~~~~~

:code:`-config` example

.. code-block:: yaml

    # The id of the project, which must already exist and be available in
    # the stea database. In the Stea documentation this is called "AlternativeId".
    project-id: 4782
    project-version: 1


    # All information in stea is versioned with a timestamp. When we request a
    # calculation we must specify wich date we wish to use to fetch configuration
    # information for assumptions like e.g. the oil price.
    config-date: 2018-07-01 12:00:00


    # The stea web client works by *adjusting* the profiles in an existing
    # stea project which has already been defined. That implies that all
    # profiles added in this configuration file should already be part of
    # the project. To match the profiles specified here with the profiles in
    # the project we must give a id for the profiles.

    # The profiles keyword is used to enter profile data explicitly in the
    # configuration file. Each profile is identified with an id from the
    # existing stea project, a start date and the actual data.

    profiles:
        <ecl_profile_id>:
           start-year: 2018
           data: [100, 200, 300]

    # Profiles which are calculated directly from an eclipse simulation are
    # listed with the ecl-profiles key. Each profile is identified with an id
    # from the stea project and an eclipe key like 'FOPT'. By default the stea
    # client will calculate a profile from the full time range of the simulated
    # data, but you can optionally use the keywords start-year and end-year to
    # limit the time range.
    ecl-profiles:
      <ecl_profile_id>:
         ecl-key: FOPT

      <ecl_profile_id>:
         ecl-key: FGPT
         start-year: 2020
         end-year: 2030

      profile_comment_in_stea:
         ecl-key: FWPT
         glob_mult: 1.1

      another_profile_comment_in_stea:
         ecl-key: FWPT
         mult: [ 1.1, 2, 0 ]

    # What do you want stea to calculate
    results:
       - NPV

"""


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    if options.lint:
        args_parser.exit()

    for res, value in (
        stea.calculate(options.config).results(stea.SteaKeys.CORPORATE).items()
    ):
        with open(f"{res}", "w") as ofh:
            ofh.write(f"{value}\n")


if __name__ == "__main__":
    main_entry_point()
