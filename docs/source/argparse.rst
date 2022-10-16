##################
Forward Model Jobs
##################


Drill Planner
=============

.. argparse::
    :module: spinningjenny.jobs.fm_drill_planner.parser.py
    :func: build_argument_parser
    :prog: fm_drill_planner


Net Present Value
=================

.. argparse::
    :module: spinningjenny.jobs.fm_npv.parser.py
    :func: build_argument_parser
    :prog: fm_npv


Recovery Factor
===============

.. argparse::
    :module: spinningjenny.jobs.fm_rf.parser.py
    :func: build_argument_parser
    :prog: fm_rf


Well Constraints
================

.. argparse::
    :module: spinningjenny.jobs.fm_well_constraints.parser.py
    :func: build_argument_parser
    :prog: fm_well_constraints
