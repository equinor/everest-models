#!/usr/bin/env python

from setuptools import setup, find_packages
import ruamel.yaml as yaml


def entry_point_strings():
    with open("spinningjenny/share/entry_points.yml") as fh:
        eps = yaml.safe_load(fh)

    return ["fm_{} = {}".format(k, v) for k, v in eps.items()]


setup(
    name="spinningjenny",
    packages=find_packages(include=["spinningjenny*"]),
    package_data={
        "spinningjenny": [
            "share/entry_points.yml",
            "share/forwardmodels/*",
            "share/npv/*",
        ]
    },
    description="Module containing a collection of jobs for ERT",
    author="Equinor ASA",
    url="https://github.com/equinor/spinningjenny",
    install_requires=[
        "configsuite>=0.6.2",
        "ecl",
        "jinja2",
        "numpy",
        "ortools",
        "protobuf",
        "ruamel.yaml",
        "stea",
    ],
    test_suite="tests",
    use_scm_version={"write_to": "spinningjenny/version.py"},
    classifiers=[
        "Programming language :: Python",
        "Programming language :: Python :: 3.8",
        "Programming language :: Python :: 3.9",
        "Programming language :: Python :: 3.10",
    ],
    entry_points={
        "console_scripts": entry_point_strings(),
        "everest": [
            "spinningjenny = spinningjenny.everest_hooks",
        ],
    },
)
