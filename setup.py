#!/usr/bin/env python

from setuptools import setup

setup(name='spinningjenny',
      packages=[
          'share',
          'share/spinningjenny',
          'share/spinningjenny/forwardmodels',
          'spinningjenny',
          'spinningjenny/script',
      ],
      description='Module containing a collection of jobs for ERT',
      author='Equinor ASA',
      url='https://github.com/equinor/spinningjenny',
      setup_requires=['pytest-runner'],
      tests_require=[
          'pytest',
          'decorator',
      ],
      classifisers=[
          'Programming language :: Python',
          'Programming language :: Python :: 2.7',
          'Programming language :: Python :: 3.5',
          'Programming language :: Python :: 3.6'
      ],
      entry_points={
          'console_scripts': [
              'fm_npv = spinningjenny.script.npv:main_entry_point',
              'fm_strip_dates = spinningjenny.script.strip_dates:main_entry_point',
              'fm_rf = spinningjenny.script.rf:main_entry_point',
          ],
      })
