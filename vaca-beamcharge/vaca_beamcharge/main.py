"""Definition of main application."""
import time as _time

import mathphys

import vaca_beamcharge.pvs as _pvs
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
            description=section + 'beam charge soft IOC',
            version=_pvs._VERSION,
            prefix=_pvs._PREFIX)
        _siriuspy.util.save_ioc_pv_list(
            'vaca-ioc-'+section.lower()+'-beamcharge',
            (_pvs._PREFIX_SECTOR, _pvs._PREFIX_VACA), App.pvs_database)

        self._driver = driver
        self._beam_charge = BeamCharge(charge=_pvs._INIT_CHARGE,
                                       nr_bunches=_pvs._NR_BUNCHES)
        self._beam_charge.set_lifetimes(
            elastic=_pvs._LT_ELASTIC, inelastic=_pvs._LT_INELASTIC,
            quantum=_pvs._LT_QUANTUM,
            touschek_coefficient=_pvs._TOUSCHEK_COEFF)

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
        return None

    def write(self, reason, value):
        """Write value to reason."""
        return None

    def _update(self):
        time_interval = _pvs._REV_PERIOD

        currents_BbB = self._beam_charge.current_BbB(time_interval)
        currents_mA = [bunch_current / _u.mA for bunch_current in currents_BbB]
        current_mA = self._beam_charge.current(time_interval) / _u.mA

        for pv in _pvs._PVS:
            self._driver.setParam(pv + ':Current-Mon', current_mA)
            self._driver.setParam(pv + ':BbBCurrent-Mon', currents_mA)
        self._driver.updatePVs()
