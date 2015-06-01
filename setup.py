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
    package_data={'va': ['VERSION']},

    install_requires=[
        'numpy>=1.8.2',
        'termcolor>=1.1.0',
        'pcaspy==0.5.1',
        'lnls>=0.1.0',
        'mathphys>=0.1.0',
        'pyaccel>=0.3.0',
        'sirius>=0.1.0'
    ],
    dependency_links=[
        'https://github.com/lnls-fac/lnls/archive/v0.1.0.tar.gz#egg=lnls-0.1.0',
        'https://github.com/lnls-fac/mathphys/archive/v0.1.0.tar.gz#egg=mathphys-0.1.0',
        'https://github.com/lnls-fac/pyaccel/archive/v0.3.0.tar.gz#egg=pyaccel-0.3.0',
        'https://github.com/lnls-fac/sirius/archive/v0.1.0.tar.gz#egg=sirius-0.1.0'
    ],
    scripts=[
        'scripts/sirius-vaca.py',
    ],
    script_dir='/usr/local/bin'
)
