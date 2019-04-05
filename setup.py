#!/usr/bin/env python

from setuptools import setup


setup(
    name="spinningjenny",
    packages=[
        "share",
        "share/spinningjenny",
        "share/spinningjenny/forwardmodels",
        "spinningjenny",
        "spinningjenny/script",
    ],
    description="Module containing a collection of jobs for ERT",
    author="Equinor ASA",
    url="https://github.com/equinor/spinningjenny",
    install_requires=["stea"],
    setup_requires=["pytest-runner"],
    test_suite="tests",
    tests_require=["pytest", "decorator", "mock", 'black ; python_version>="3.6"'],
    classifisers=[
        "Programming language :: Python",
        "Programming language :: Python :: 2.7",
        "Programming language :: Python :: 3.5",
        "Programming language :: Python :: 3.6",
    ],
    entry_points={
        "console_scripts": [
            "fm_drill_planner = spinningjenny.script.drill_planner:main_entry_point",
            "fm_npv = spinningjenny.script.npv:main_entry_point",
            "fm_rf = spinningjenny.script.rf:main_entry_point",
            "fm_stea = spinningjenny.script.stea_fmu:stea_main",
            "fm_strip_dates = spinningjenny.script.strip_dates:main_entry_point",
        ]
    },
)
