"""Beam Charge PVs definition."""
from siriuspy.envars import vaca_prefix as _vaca_prefix

_PREFIX_VACA = _vaca_prefix
_PREFIX_SECTOR = None
_PREFIX = None

_VERSION = '0.0.1'

# Must be parametrized to SI and BO
_NR_BUNCHES = 864
_LT_ELASTIC = 20*60*60  # [s]
_LT_INELASTIC = 30*60*60  # [s]
_LT_QUANTUM = float('inf')  # [s]
_TOUSCHEK_COEFF = 36.31  # [1/(C*s)]
_REV_PERIOD = 1.7e-6  # [s]
_INIT_CURRENT = 300e-3  # [A]
_INIT_CHARGE = _INIT_CURRENT*_REV_PERIOD

_PVS = []


def ioc_setting(section):
    """Set global variables according to section."""
    global _PVS, _PREFIX, _PREFIX_SECTOR
    if section == "SI":
        _PVS = ['13C4:DI-DCCT', '14C4:DI-DCCT']
        _PREFIX_SECTOR = "SI-"
    elif section == "BO":
        _PVS = ['35D:DI-DCCT']
        _PREFIX_SECTOR = "BO-"
    else:
        raise AttributeError("Undefined section")
    _PREFIX = _PREFIX_VACA + _PREFIX_SECTOR


def get_ioc_database():
    """Return DI database."""
    pv_database = {}
    pv_database['Version-Cte'] = \
        {'type': 'str', 'value': _VERSION, 'scan': 0.1}

    for pv in _PVS:
        pv_database[pv + ':Current-Mon'] = \
            {'type': 'float', 'unit': 'mA', 'value': 0.0}
        pv_database[pv + ':BbBCurrent-Mon'] = \
            {'type': 'float', 'count': _NR_BUNCHES}

    return pv_database
