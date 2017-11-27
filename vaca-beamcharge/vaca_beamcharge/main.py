"""Definition of main application."""
import time as _time
import random as _random
import math as _math

import mathphys

import vaca_beamcharge.pvs as _pvs
import vaca_beamcharge.pvs_fake as _pvs_fake
import vaca_beamcharge.parameters as _parameters
from .beam_charge import BeamCharge
import siriuspy as _siriuspy


_u = mathphys.units


class App:
    """Main application."""

    pvs_database = None

    def __init__(self, driver):
        """Init."""
        section = _pvs._PREFIX_SECTOR[:-1]
        _siriuspy.util.print_ioc_banner(
            ioc_name=section + ' Beam Charge',
            db=_pvs.get_ioc_database(),
            description=section + ' beam charge soft IOC',
            version=_pvs._VERSION,
            prefix=_pvs._PREFIX)
        _siriuspy.util.save_ioc_pv_list(
            'vaca-ioc-'+section.lower()+'-beamcharge',
            (_pvs._PREFIX_SECTOR, _pvs._PREFIX_VACA), App.pvs_database)

        self._driver = driver
        self._beam_charge = BeamCharge(
            charge=_pvs._INIT_CHARGE,
            nr_bunches=_parameters._NR_BUNCHES,
            period=_parameters._REV_PERIOD,
            lifetime_elastic=_pvs._LT_ELASTIC,
            lifetime_inelastic=_pvs._LT_INELASTIC,
            lifetime_quantum=_pvs._LT_QUANTUM,
            lifetime_touschek_ref=_pvs._LT_TOUSCHEK_REF)

        # Set object responsible for fake pvs
        self._PVFAKE = _pvs._PVFAKE
        self._PVFAKE.set_driver(self._driver)
        self._PVFAKE.set_beam_charge(self._beam_charge)

    @staticmethod
    def init_class():
        """Init class."""
        App.pvs_database = _pvs.get_ioc_database()

    @property
    def driver(self):
        """Driver."""
        return self._driver

    def process(self, interval):
        """Sleeps."""
        _time.sleep(interval)

    def read(self, reason):
        """Read from IOC DB."""
        if 'Version-Cte' in reason:
            self._update()
            return _pvs._VERSION

        if self._PVFAKE.is_fake(reason):
            return self._PVFAKE.read(reason)

        return None

    def write(self, reason, value):
        """Write value to reason."""
        if self._PVFAKE.is_fake(reason):
            self._PVFAKE.write(reason, value)
        return None

    def _update(self):
        # Fluctuation
        bfluc = _random.gauss(
            0, _pvs_fake._CURRENT_FLUC_STD) / _math.sqrt(_parameters._NR_BUNCHES)

        currents_BbB = self._beam_charge.current_BbB
        currents_mA = \
            [bunch_current / _u.mA + bfluc for bunch_current in currents_BbB]
        current_mA = sum(currents_mA)

        for pv in _pvs._PVS:
            self._driver.setParam(pv + ':BbBCurrent-Mon', currents_mA)
            self._driver.setParam(pv + ':Current-Mon', current_mA)

        lifetime = self._beam_charge.lifetime
        # print(self._beam_charge)
        lifetime_BbB = self._beam_charge.lifetime
        self._driver.setParam(self._PVFAKE.FakeLifetimeMon, lifetime)
        self._driver.setParam(self._PVFAKE.FakeBbBLifetimeMon, lifetime_BbB)
        self._driver.updatePVs()
