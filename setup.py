#!/usr/bin/env python

from setuptools import setup, find_packages
import yaml


def entry_point_strings():
    with open("share/entry_points.yml") as fh:
        eps = yaml.safe_load(fh)

    return ["fm_{} = {}".format(k, v) for k, v in eps.items()]


setup(
    name="spinningjenny",
    packages=find_packages(include=["spinningjenny*", "share*"]),
    package_data={
        "share": [
            "entry_points.yml",
            "spinningjenny/forwardmodels/*",
            "spinningjenny/npv/*",
        ]
    },
    description="Module containing a collection of jobs for ERT",
    author="Equinor ASA",
    url="https://github.com/equinor/spinningjenny",
    install_requires=[
        "stea",
        "configsuite>=0.6.2",
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
    entry_points={
        "console_scripts": entry_point_strings(),
        "everest": [
            "spinningjenny = spinningjenny.everest_hooks",
        ],
    },
)
