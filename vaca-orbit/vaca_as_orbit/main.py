"""Main Module of the program."""

import time as _time
import numpy as _np
import logging as _log
from pcaspy import Driver as _PCasDriver
import siriuspy.csdevice.orbitcorr as _csorb
from siriuspy.thread import QueueThread as _Queue
from .util import CHCV as _CHCV, RFCtrl as _RFCtrl, Timing as _Timing
from siriuspy.callbacks import Callback as _Callback

INTERVAL = 0.1


class App(_Callback):
    """Main Class of the IOC."""

    def get_database(self):
        """Get the database of the class."""
        db = dict()
        for c in self._chcvs:
            db.update(c.get_database())
        db.update(self._rf_ctrl.get_database())
        db.update(self._timing.get_database())
        return db

    def __init__(self, acc, callback=None):
        """Initialize Object."""
        self._acc = acc
        self._const = _csorb.get_consts(acc)
        self._driver = None
        self._queue = _Queue()
        self._queue.start()

        self.orbit = _np.random.normal(0, 2e6, 2*self._const.NR_BPMS)
        self.matrix = _np.random.rand(
                            2*self._const.NR_BPMS, self._const.NR_CORRS)

        self._names = self._const.CH_NAMES + self._const.CV_NAMES
        self._chcvs = len(self._names)*[0]
        for i, dev in enumerate(self._names):
            self._chcvs[i] = _CHCV(
                dev, i,
                ioc_callback=self._schedule_update,
                orb_callback=self._update_orbit)
        self._rf_ctrl = _RFCtrl(
                len(self._names),
                ioc_callback=self._schedule_update,
                orb_callback=self._update_orbit)
        self._timing = _Timing(
                acc,
                ioc_callback=self._schedule_update,
                trig_callback=self._timing_trigger)
        self.add_callback(self._schedule_update)
        self._database = self.get_database()

    @property
    def acc(self):
        return self._acc

    @property
    def driver(self):
        """Set the driver of the instance."""
        return self._driver

    @driver.setter
    def driver(self, driver):
        if isinstance(driver, _PCasDriver):
            self._driver = driver

    def write(self, reason, value):
        """Write value in database."""
        if not self._isValid(reason, value):
            return False
        fun_ = self._database[reason].get('fun_set_pv')
        if fun_ is None:
            _log.warning('Write unsuccessful. PV ' +
                         '{0:s} does not have a set function.'.format(reason))
            return False
        ret_val = fun_(value)
        if ret_val:
            _log.debug('Write complete.')
        else:
            value = self._driver.getParam(reason)
            _log.warning('Unsuccessful write of PV ' +
                         '{0:s}; value = {1:s}.'.format(reason, str(value)))
        self._schedule_update(reason, value)

    def process(self):
        """Run continuously in the main thread."""
        t0 = _time.time()
        tf = _time.time()
        dt = INTERVAL - (tf-t0)
        if dt > 0:
            _time.sleep(dt)
        else:
            _log.debug('App: check took {0:f}ms.'.format((tf-t0)*1000))

    def _schedule_update(self, pvname, value, **kwargs):
        self._queue.add_callback(self._update_driver, pvname, value, **kwargs)

    def _update_driver(self, pvname, value, **kwargs):
        reason = self._prefix + pvname
        self._driver.setParam(reason, value)
        self._driver.updatePV(reason)

    def _isValid(self, reason, value):
        if reason.endswith(('-Sts', '-RB', '-Mon')):
            _log.debug('App: PV {0:s} is read only.'.format(reason))
            return False
        enums = self._database[reason].get('enums')
        if enums is not None:
            if isinstance(value, int):
                if value >= len(enums):
                    _log.warning('App: value {0:d} too large '.format(value) +
                                 'for PV {0:s} of type enum'.format(reason))
                    return False
            elif isinstance(value, str):
                if value not in enums:
                    _log.warning('Value {0:s} not permited'.format(value))
                    return False
        return True

    def _update_orbit(self, corrs_idx, corrs_deltas, **kw):
        self._orbit += _np.dot(self._matrix[:, corrs_idx], corrs_deltas)

    def _timing_trigger(self, **kw):
        for c in self._chcvs:
            c.timing_trigger()
