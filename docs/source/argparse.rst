##################
Forward Model Jobs
##################


Drill Planner
=============

.. argparse::
    :filename: jobs/fm_drill_planner/cli.py
    :func: scheduler_parser
    :prog: fm_drill_planner


Net Present Value
=================

.. argparse::
    :filename: jobs/fm_npv/cli.py
    :func: _build_parser
    :prog: fm_npv


Recovery Factor
===============

.. argparse::
    :filename: jobs/fm_rf/cli.py
    :func: rf_parser
    :prog: fm_rf


Well Constraints
================

.. argparse::
    :filename: jobs/fm_well_constraints/cli.py
    :func: well_constraint_parser
    :prog: fm_well_constraints
