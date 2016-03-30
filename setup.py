#!/usr/bin/env python3

from setuptools import setup

with open('VERSION','r') as _f:
    __version__ = _f.read().strip()

setup(
    name='va',
    version=__version__,
    author='lnls-fac',
    description='Virtual accelerator with channel access server',
    url='https://github.com/lnls-fac/va',
    download_url='https://github.com/lnls-fac/va',
    license='MIT License',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering'
    ],
    packages=['va'],
    package_data={'va': ['VERSION', 'pvs/*.py']},
    scripts=['scripts/sirius-vaca.py', 'scripts/sirius-state-save.py', 'scripts/sirius-state-load.py'],
    zip_safe=False
)
