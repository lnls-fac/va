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

fake_pvs = None


def ioc_setting(section):
    """Set global variables according to section."""
    global _PVS, _PREFIX, _PREFIX_SECTOR, fake_pvs
    if section == "SI":
        _PVS = ['13C4:DI-DCCT', '14C4:DI-DCCT']
        _PREFIX_SECTOR = "SI-"
    elif section == "BO":
        _PVS = ['35D:DI-DCCT']
        _PREFIX_SECTOR = "BO-"
    else:
        raise AttributeError("Undefined section")
    _PREFIX = _PREFIX_VACA + _PREFIX_SECTOR
    fake_pvs = FakePvs()


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

    # Add fake pvs to db
    fake_pvs.update_db(pv_database)

    return pv_database


class FakePvs:
    """Fake Beam Charge IOC PVs."""

    FakeDeltaCurrentSP = "FakeDeltaCurrent-SP"
    FakeBbBDeltaCurrentSP = "FakeBbBDeltaCurrent-SP"
    FakeElasticSP = "FakeLTElastic-SP"
    FakeInelasticSP = "FakeLTInelastic-SP"
    FakeQuantumSP = "FakeLTQuantum-SP"
    FakeToucheskSP = "FakeLTTouschek-SP"
    FakeCurrLTMon = "FakeCurrLT-Mon"

    def __init__(self):
        """Set fake pvs."""
        self._driver = None
        self._beam_charge = None

        self._db = None
        self._writable_fake_pvs = None
        self._readable_fake_pvs = None
        # Set fake pvs and fake db
        self._set_fake_pvs()

    def set_driver(self, driver):
        """Set driver."""
        self._driver = driver

    def set_beam_charge(self, beam_charge):
        """Set beam charge object."""
        self._beam_charge = beam_charge

    def read(self, reason):
        """Read from beam charge object."""
        if reason in self._readable_fake_pvs:
            return self._read_beam_charge(reason)

    def write(self, reason, value):
        """Write to beam charge object."""
        if reason in self._writable_fake_pvs:
            self._set_beam_charge(reason, value)

    def update_db(self, db):
        """Update database with fake pvs."""
        db.update(self._db)

    def is_fake(self, reason):
        """Return wether reason is a fake PV."""
        if reason in self._writable_fake_pvs or \
                reason in self._readable_fake_pvs:
            return True
        return False

    def _set_fake_pvs(self):
        self._readable_fake_pvs = set()
        self._writable_fake_pvs = set()
        self._db = {}
        # Fake Set point
        self._writable_fake_pvs.add(FakePvs.FakeDeltaCurrentSP)
        self._db[FakePvs.FakeDeltaCurrentSP] = \
            {'type': 'float', 'unit': 'C', 'value': 0.0}
        self._writable_fake_pvs.add(FakePvs.FakeBbBDeltaCurrentSP)
        self._db[FakePvs.FakeBbBDeltaCurrentSP] = \
            {'type': 'float', 'count': _NR_BUNCHES}
        self._writable_fake_pvs.add(FakePvs.FakeElasticSP)
        self._db[FakePvs.FakeElasticSP] = {'type': 'float', 'value': 0.0}
        self._writable_fake_pvs.add(FakePvs.FakeInelasticSP)
        self._db[FakePvs.FakeInelasticSP] = {'type': 'float', 'value': 0.0}
        self._writable_fake_pvs.add(FakePvs.FakeQuantumSP)
        self._db[FakePvs.FakeQuantumSP] = {'type': 'float', 'value': 0.0}
        self._writable_fake_pvs.add(FakePvs.FakeToucheskSP)
        self._db[FakePvs.FakeToucheskSP] = {'type': 'float', 'value': 0.0}
        # Fake readbacks
        self._readable_fake_pvs.add(FakePvs.FakeCurrLTMon)
        self._db[FakePvs.FakeCurrLTMon] = {'type': 'float', 'value': 0.0}

    def _read_beam_charge(self, reason):
        if self._beam_charge is not None:
            if reason == FakePvs.FakeCurrLTMon:
                return float(self._beam_charge.lifetime_total)

    def _set_beam_charge(self, reason, value):
        if self._beam_charge is not None:
            if reason == FakePvs.FakeDeltaCurrentSP:
                # Convert to charge and set
                nr_bunches = self._beam_charge.nr_bunches
                current_list = [value/nr_bunches] * nr_bunches
                charge_list = [current*_REV_PERIOD for current in current_list]
                self._beam_charge.inject(charge_list)
            elif reason == FakePvs.FakeBbBDeltaCurrentSP:
                # Convert to charge and set
                nr_bunches = self._beam_charge.nr_bunches
                current_list = value
                charge_list = [current*_REV_PERIOD for current in current_list]
                self._beam_charge.inject(charge_list)
            elif reason == FakePvs.FakeElasticSP:
                self._beam_charge.elastic_lifetime = value
            elif reason == FakePvs.FakeInelasticSP:
                self._beam_charge.inelastic_lifetime = value
            elif reason == FakePvs.FakeQuantumSP:
                self._beam_charge.quantum_lifetime = value
            elif reason == FakePvs.FakeToucheskSP:
                self._beam_charge.touschek_coefficient = value
            self._driver.setParam(reason, value)
