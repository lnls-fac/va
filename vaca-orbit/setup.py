#!/usr/bin/env python-sirius
"""Package installer."""

from setuptools import setup

with open('VERSION', 'r') as _f:
    __version__ = _f.read().strip()

setup(
    name='vaca_as_orbit',
    version=__version__,
    author='lnls-fac',
    description='VACA IOC for simulating the orbit .',
    url='https://github.com/lnls-fac/va',
    download_url='https://github.com/lnls-fac/va',
    license='GNU GPLv3',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering'
    ],
    packages=['vaca_as_orbit'],
    package_data={'vaca_as_orbit': ['VERSION']},
    scripts=['scripts/vaca-ioc-si-orbit.py',
             'scripts/vaca-ioc-bo-orbit.py'],
    zip_safe=False
)
