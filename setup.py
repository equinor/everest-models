#!/usr/bin/env python

from setuptools import setup, find_packages
from spinningjenny.bin import entry_points


setup(
    name="spinningjenny",
    packages=find_packages(include=["spinningjenny*", "share*"]),
    package_data={"share": ["spinningjenny/forwardmodels/*", "spinningjenny/npv/*"]},
    description="Module containing a collection of jobs for ERT",
    author="Equinor ASA",
    url="https://github.com/equinor/spinningjenny",
    install_requires=["stea"],
    setup_requires=["pytest-runner", "setuptools_scm"],
    test_suite="tests",
    use_scm_version={"write_to": "spinningjenny/version.py"},
    tests_require=[
        "pytest==4.6.4; python_version<='2.7'",
        "pytest; python_version>='3.5'",
        "decorator",
        "mock",
        'black; python_version>="3.6"',
    ],
    classifiers=[
        "Programming language :: Python",
        "Programming language :: Python :: 2.7",
        "Programming language :: Python :: 3.5",
        "Programming language :: Python :: 3.6",
    ],
    entry_points={"console_scripts": entry_points()},
)
