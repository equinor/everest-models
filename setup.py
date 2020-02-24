#!/usr/bin/env python

from setuptools import setup, find_packages


def entry_point_strings():
    eps = {
        "drill_planner": "spinningjenny.script.fm_drill_planner:main_entry_point",
        "npv": "spinningjenny.script.fm_npv:main_entry_point",
        "rf": "spinningjenny.script.fm_rf:main_entry_point",
        "schmerge": "spinningjenny.script.fm_schmerge:main_entry_point",
        "stea": "spinningjenny.script.fm_stea:main_entry_point",
        "strip_dates": "spinningjenny.script.fm_strip_dates:main_entry_point",
        "well_constraints": "spinningjenny.script.fm_well_constraints:main_entry_point",
        "add_templates": "spinningjenny.script.fm_add_templates:main_entry_point",
        "well_filter": "spinningjenny.script.fm_well_filter:main_entry_point",
        "interpret_well_drill": "spinningjenny.script.fm_interpret_well_drill:main_entry_point",
        "extract_summary_data": "spinningjenny.script.fm_extract_summary_data:main_entry_point",
    }
    return ["fm_{} = {}".format(k, v) for k, v in eps.items()]


setup(
    name="spinningjenny",
    packages=find_packages(include=["spinningjenny*", "share*"]),
    package_data={"share": ["spinningjenny/forwardmodels/*", "spinningjenny/npv/*"]},
    description="Module containing a collection of jobs for ERT",
    author="Equinor ASA",
    url="https://github.com/equinor/spinningjenny",
    install_requires=[
        "stea",
        "configsuite>=0.3.1",
        "ortools",
        "protobuf",
        "libecl",
        "jinja2",
        "PyYAML",
    ],
    test_suite="tests",
    use_scm_version={"write_to": "spinningjenny/version.py"},
    classifiers=[
        "Programming language :: Python",
        "Programming language :: Python :: 2.7",
        "Programming language :: Python :: 3.5",
        "Programming language :: Python :: 3.6",
    ],
    entry_points={"console_scripts": entry_point_strings()},
)
