"""Fake PVs."""

import vaca_beamcharge.parameters as _parameters
import mathphys.units as _u

_FAKE_PVS_PREFIX = 'Glob:AP-VABeamCharge:'
_CURRENT_FLUC_STD = 0.0


class PVFake:
    """Fake Beam Charge IOC PVs."""

    FakeDeltaCurrentSP = _FAKE_PVS_PREFIX + "FakeDeltaCurrent-SP"
    FakeBbBDeltaCurrentSP = _FAKE_PVS_PREFIX + "FakeBbBDeltaCurrent-SP"
    FakeCurrentFluctStd = _FAKE_PVS_PREFIX + "FakeCurrentFluctStd-SP"

    FakeLTElasticSP = _FAKE_PVS_PREFIX + "FakeLTElastic-SP"
    FakeLTInelasticSP = _FAKE_PVS_PREFIX + "FakeLTInelastic-SP"
    FakeLTQuantumSP = _FAKE_PVS_PREFIX + "FakeLTQuantum-SP"
    FakeLTTouschekRefSP = _FAKE_PVS_PREFIX + "FakeLTTouschekRef-SP"

    FakeLifetimeMon = _FAKE_PVS_PREFIX + "FakeLifetime-Mon"
    FakeBbBLifetimeMon = _FAKE_PVS_PREFIX + "FakeBbBLifetime-Mon"

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
        self.write(reason=PVFake.FakeLTElasticSP,
                   value=self._beam_charge.lifetime_elastic)
        self.write(reason=PVFake.FakeLTInelasticSP,
                   value=self._beam_charge.lifetime_inelastic)
        self.write(reason=PVFake.FakeLTQuantumSP,
                   value=self._beam_charge.lifetime_quantum)
        self.write(reason=PVFake.FakeLTTouschekRefSP,
                   value=self._beam_charge.lifetime_touschek_ref)

    def read(self, reason):
        """Read from beam charge object."""
        if self.is_fake(reason):
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

        # Fake setpoints
        self._writable_fake_pvs.add(PVFake.FakeDeltaCurrentSP)
        self._db[PVFake.FakeDeltaCurrentSP] = \
            {'type': 'float', 'unit': 'mA', 'value': 0.0}
        self._writable_fake_pvs.add(PVFake.FakeBbBDeltaCurrentSP)
        self._db[PVFake.FakeBbBDeltaCurrentSP] = {
            'type': 'float', 'unit': 'mA', 'count': _parameters._NR_BUNCHES,
            'value': [0.0 for _ in range(_parameters._NR_BUNCHES)]
        }
        self._writable_fake_pvs.add(PVFake.FakeLTElasticSP)
        self._db[PVFake.FakeLTElasticSP] = {
            'type': 'float', 'unit': 's', 'value': 0.0
        }
        self._writable_fake_pvs.add(PVFake.FakeLTInelasticSP)
        self._db[PVFake.FakeLTInelasticSP] = {
            'type': 'float', 'unit': 's', 'value': 0.0
        }
        self._writable_fake_pvs.add(PVFake.FakeLTQuantumSP)
        self._db[PVFake.FakeLTQuantumSP] = {
            'type': 'float', 'unit': 's', 'value': 0.0
        }
        self._writable_fake_pvs.add(PVFake.FakeLTTouschekRefSP)
        self._db[PVFake.FakeLTTouschekRefSP] = {
            'type': 'float', 'unit': 's', 'value': 0.0
        }
        self._writable_fake_pvs.add(PVFake.FakeCurrentFluctStd)
        self._db[PVFake.FakeCurrentFluctStd] = {
            'type': 'float', 'unit': 's', 'value': 0.0
        }

        # Fake readbacks
        self._readable_fake_pvs.add(PVFake.FakeLifetimeMon)
        self._readable_fake_pvs.add(PVFake.FakeBbBLifetimeMon)
        self._db[PVFake.FakeLifetimeMon] = {
            'type': 'float', 'unit': 's', 'value': 0.0
        }
        self._db[PVFake.FakeBbBLifetimeMon] = {
            'type': 'float', 'unit': 's', 'count': _parameters._NR_BUNCHES,
            'value': [0.0 for _ in range(_parameters._NR_BUNCHES)]
        }

    def _read_beam_charge(self, reason):
        if self._beam_charge is not None:
            if reason == PVFake.FakeLifetimeMon:
                return float(self._beam_charge.lifetime)
        return None

    def _set_beam_charge(self, reason, value):
        if self._beam_charge is not None:
            if reason == PVFake.FakeDeltaCurrentSP:
                # Convert to charge and set
                nr_bunches = self._beam_charge.nr_bunches
                current_mA = [_u.mA*value/nr_bunches] * nr_bunches
                charge_list = [current*_parameters._REV_PERIOD for
                               current in current_mA]
                self._beam_charge.inject(charge_list)
            elif reason == PVFake.FakeBbBDeltaCurrentSP:
                # Convert to charge and set
                nr_bunches = self._beam_charge.nr_bunches
                current_list = value
                charge_list = [current*_parameters._REV_PERIOD for
                               current in current_list]
                self._beam_charge.inject(charge_list)
            elif reason == PVFake.FakeLTElasticSP:
                self._beam_charge.lifetime_elastic = value
            elif reason == PVFake.FakeLTInelasticSP:
                self._beam_charge.lifetime_inelastic = value
            elif reason == PVFake.FakeLTQuantumSP:
                self._beam_charge.lifetime_quantum = value
            elif reason == PVFake.FakeLTTouschekRefSP:
                self._beam_charge.lifetime_touschek_ref = value
            elif reason == PVFake.FakeCurrentFluctStd:
                global _CURRENT_FLUC_STD
                _CURRENT_FLUC_STD = value * _u.mA
            self._driver.setParam(reason, value)
            self._driver.updatePVs()
