# VACA - Virtual Accelerator with Channel Access

A virtual accelerator implemented with EPICS channel access, for testing high level machine applications (HLA).

# V1.5.0

This version was used until Jan. 2018, when Sirius sunsystems started being integrated and HLA could be tested using real hardware.

# V2.0.0

This is a ressurect version of VACA that employs the current state of sirius' python packages, as they are being used in sirius control system.

## dependencies (repos):

 - siriuspy: https://github.com/lnls-sirius/dev-packages
 - mathphys: https://github.com/lnls-fac/mathphys
 - lnls:     https://github.com/lnls-fac/lnls
 - pymodels: https://github.com/lnls-fac/pymodels/tree/vaca-ilsf
 - pyaccel:  https://github.com/lnls-fac/pyaccel/tree/fix-optics
 - trackcpp: https://github.com/lnls-fac/trackcpp
 - csconst:  https://github.com/lnls-sirius/control-system-constants
 - hla:      https://github.com/lnls-sirius/hla/tree/fix-ps-windows-prefix   

## Installation

To install `va` python package and `vaca-ioc.py` script in the system, run `./setup.py develop` or `./setup.py install`. A web server should be running in order to provide static data files for VACA. Files from `control-system-constants` repository should be located in the top of the web server public folder.

## Running VACA

- Environment variable `SIRIUS_URL_CONSTS`should be set to point to the web server top URL. (for example, `export SIRIUS_URL_CONST=https://127.0.0.1`).
- Run `vaca-ioc.py --pvs`: this will save PV files in the local folder. PVs being served with VACA can be looked up in these files.
- One can select set of accelerator models to be used with environment variable `LAB_PREFIX`. It is overriden with command line option `--lab`. For example,  `vaca-ioc.py --lab ilsf`
- To add fluctuation to PV values one can define update frequency in Hz with env variable `VACA_UPDATE` or argument `--update`.

## Virtual machine

Currently timing subsystem is broken. No timing device/PV is available. Consequently the injection process is not working. But fake PVs (for `VA-Control` devices) were implemented to add beam currents to circular accelerators. Beam position readouts are working, as well as magnet power supplies current settings.
`''` is the standard PV prefix. It can be overridden with `VACA_PREFIX` env variable. A `'-'` is postpended to the prefix so that `VACA_PREFIX='VA'` with generate PV names that start with `VA-`. Env variable `VACA_PREFIX` is overridden by VACA command line option `--prefix`.

Examples on how to interact with virtual machine:

- To read beam current in booster: `caget VA-BO-35D:DI-DCCT:Current-Mon`
- To add 10 mA beam current to booster: `caput VA-BO-Glob:VA-Control:BeamCurrentAdd-SP 10`
- To read beam current in booster (with beam): `caget VA-BO-35D:DI-DCCT:Current-Mon`
- To read a beam position in the booster: `caget VA-BO-01U:DI-BPM:PosX-Mon`
- To set 0.01 A to a 150 MeV booster corrector power supply: `caput VA-BO-01U:PS-CH:Current-SP 0.01`
- To read a beam position in the booster (after kick): `caget VA-BO-01U:DI-BPM:PosX-Mon`
- To add 10 mA beam current to ring (fake): `caput VA-SI-Glob:VA-Control:BeamCurrentAdd-SP 10`
- To read beam current in ring (with beam): `caget VA-SI-13C4:DI-DCCT:Current-Mon`
- To read beam position in the ring: `caget VA-SI-01M2:DI-BPM:PosX-Mon`
- To set 0.1 A to a ring corrector power supply: `caput VA-SI-01M2:PS-CH:Current-SP 0.1`
- To read beam position in the ring (after kick): `caget VA-SI-01M2:DI-BPM:PosX-Mon`
- To quit VACA: `caput VA-AS-Glob:VA-Control:Quit-Cmd 1`

