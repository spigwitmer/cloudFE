#!/usr/bin/env python

from setuptools import setup

setup(
  name='cloudFE',
  version='0.1',
  packages=['cloudfe'],
  description='Game cloud storage frontend',
  license='MIT',
  url='https://github.com/batteryshark/cloudFE',
  classifiers=[],
  install_requires=[
    'cherrypy',
    'google-api-python-client',
    ],
  entry_points={
    'console_scripts': [
      'cloudfe = cloudfe.cloudFE:main',
      'cloudfe_dbgen = cloudfe.cfe_dbgen:run'
      ]
    }
  )
