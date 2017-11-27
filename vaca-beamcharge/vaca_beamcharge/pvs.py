"""Beam Charge PVs definition."""
from siriuspy.envars import vaca_prefix as _vaca_prefix
import vaca_beamcharge.pvs_fake as _pvs_fake
import vaca_beamcharge.parameters as _parameters

_PREFIX_VACA = _vaca_prefix
_PREFIX_SECTOR = None
_PREFIX = None

_VERSION = '0.0.1'

_CURRENT_FLUC_STD = 0.0

# Must be parametrized to SI and BO
_LT_ELASTIC = None
_LT_INELASTIC = None
_LT_QUANTUM = None
_LT_TOUSCHEK_REF = None
_INIT_CURRENT = None
_INIT_CHARGE = None
_PVS = []
_PVFAKE = None


def ioc_setting(section):
    """Set global variables according to section."""
    global _LT_ELASTIC, _LT_INELASTIC, _LT_QUANTUM, _LT_TOUSCHEK_REF
    global _INIT_CURRENT, _INIT_CHARGE
    global _PVS, _PREFIX, _PREFIX_SECTOR, _PVFAKE, _FAKE_PVS_PREFIX
    if section == 'SI':
        _PVS = ['13C4:DI-DCCT', '14C4:DI-DCCT']
        _PREFIX_SECTOR = 'SI-'
        _parameters._NR_BUNCHES = 864
        _parameters._REV_PERIOD = 1.7291829520281e-6  # [s]
        _LT_ELASTIC = 20*60*60  # [s]
        _LT_INELASTIC = 30*60*60  # [s]
        _LT_QUANTUM = float('inf')  # [s]
        _LT_TOUSCHEK_REF = (25/6)*60*60  # [s - toushek lifetime @ 1mA bunch]
        _INIT_CURRENT = 300e-3  # [A]
    elif section == 'BO':
        _PVS = ['35D:DI-DCCT']
        _PREFIX_SECTOR = 'BO-'
        _parameters._NR_BUNCHES = 828
        _parameters._REV_PERIOD = 1.6571464489841e-6  # [s]
        _LT_ELASTIC = 20*60*60  # [s]
        _LT_INELASTIC = 30*60*60  # [s]
        _LT_QUANTUM = float('inf')  # [s]
        _LT_TOUSCHEK_REF = (25/6)*60*60  # [s - toushek lifetime @ 1mA bunch]
        _INIT_CURRENT = 1e-3  # [A]
    else:
        raise AttributeError("Undefined section")
    _INIT_CHARGE = _INIT_CURRENT*_parameters._REV_PERIOD  # [C]
    _PREFIX = _PREFIX_VACA + _PREFIX_SECTOR
    _PVFAKE = _pvs_fake.PVFake()


def get_ioc_database():
    """Return DI database."""
    pv_database = {}
    pv_database['Glob:AP-VABeamCharge:Version-Cte'] = \
        {'type': 'str', 'value': _VERSION, 'scan': 0.1}

    for pv in _PVS:
        pv_database[pv + ':Current-Mon'] = \
            {'type': 'float', 'unit': 'mA', 'value': 0.0}
        pv_database[pv + ':BbBCurrent-Mon'] = \
            {'type': 'float', 'count': _parameters._NR_BUNCHES}

    # Add fake pvs to db
    _PVFAKE.update_db(pv_database)

    return pv_database
