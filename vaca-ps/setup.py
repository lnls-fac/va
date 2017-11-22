#!/usr/bin/env python-sirius
"""Package installer."""

from setuptools import setup

with open('VERSION', 'r') as _f:
    __version__ = _f.read().strip()

setup(
    name='vaca-ps',
    version=__version__,
    author='lnls-sirius',
    description='IOC for Simulating Power Supplies.',
    url='https://github.com/lnls-fac/va',
    download_url='https://github.com/lnls-fac/va',
    license='GNU GPLv3',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering'
    ],
    packages=['vaca_ps'],
    package_data={'vaca_ps': ['VERSION']},
    scripts=['scripts/vaca-ioc-ps.py', ],
    zip_safe=False
)
