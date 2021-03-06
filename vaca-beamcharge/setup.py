#!/usr/bin/env python-sirius
"""Package installer."""

from setuptools import setup

with open('VERSION', 'r') as _f:
    __version__ = _f.read().strip()

setup(
    name='vaca-beamcharge',
    version=__version__,
    author='lnls-fac',
    description='VACA IOC for simulating the beam charge .',
    url='https://github.com/lnls-fac/va',
    download_url='https://github.com/lnls-fac/va',
    license='GNU GPLv3',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering'
    ],
    packages=['vaca_beamcharge'],
    package_data={'vaca_beamcharge': ['VERSION']},
    scripts=['scripts/vaca-ioc-si-beamcharge.py',
             'scripts/vaca-ioc-bo-beamcharge.py'],
    zip_safe=False
)
