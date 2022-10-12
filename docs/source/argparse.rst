##################
Forward Model Jobs
##################


Drill Planner
=============

.. argparse::
    :filename: spinningjenny/script/drill_planner.py
    :func: scheduler_parser
    :prog: fm_drill_planner


Net Present Value
=================

.. argparse::
    :filename: spinningjenny/script/npv.py
    :func: _build_parser
    :prog: fm_npv


Recovery Factor
===============

.. argparse::
    :filename: spinningjenny/script/rf.py
    :func: rf_parser
    :prog: fm_rf


Well Constraints
================

.. argparse::
    :filename: spinningjenny/script/well_constraints.py
    :func: well_constraint_parser
    :prog: fm_well_constraints
