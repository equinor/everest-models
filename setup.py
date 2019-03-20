#!/usr/bin/env python

from setuptools import setup

setup(name='spinningjenny',
      description='Module containing a collection of jobs for ERT',
      author='Equinor ASA',
      url='https://github.com/equinor/spinningjenny',
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      classifisers=[
          'Programming language :: Python',
          'Programming language :: Python :: 2.7',
          'Programming language :: Python :: 3.5',
          'Programming language :: Python :: 3.6'
          ])

