##################
Forward Model Jobs
##################


Drill Planner
=============

.. argparse::
    :filename: src/jobs/fm_drill_planner/parser.py
    :func: build_argument_parser
    :prog: fm_drill_planner


Net Present Value
=================

.. argparse::
    :filename: src/jobs/fm_npv/parser.py
    :func: build_argument_parser
    :prog: fm_npv


Recovery Factor
===============

.. argparse::
    :filename: src/jobs/fm_rf/parser.py
    :func: build_argument_parser
    :prog: fm_rf


Well Constraints
================

.. argparse::
    :filename: src/jobs/fm_well_constraints/parser.py
    :func: build_argument_parser
    :prog: fm_well_constraints
