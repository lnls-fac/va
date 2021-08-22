"""Module with class for PVs with fluctuations."""

import os as _os
import time as _time
import re as _re
import numpy as _np

DEFAULT_UPDATE_FREQ = float(_os.environ['VACA_UPDATE'])

class PVFluctuation:
    """Manage PVs with model-independent fluctuations."""

    def __init__(self, pvdb, pvsfluct, update_rate=DEFAULT_UPDATE_FREQ):
        self._timestamp = _time.time()
        if update_rate == 0:
            self._interval = _np.inf
            self._pvs_value, self._pvs_fluct = dict(), dict()
        else:    
            self._interval = 1/update_rate
            self._pvs_value, self._pvs_fluct = self._add_pvs_fluctuation(pvdb, pvsfluct)

    @property
    def values(self):
        new_values = dict()
        for pvname, fluct in self._pvs_fluct.items():
            sigma = self._pvs_fluct[pvname]
            fluct = sigma * _np.random.randn()
            new_values[pvname] = self._pvs_value[pvname] + fluct
        self.update_timestamp()
        return new_values

    def set_pv(self, pvname, value):
        if pvname not in self._pvs_fluct:
            return value
        else:
            self._pvs_value[pvname] = value
            sigma = self._pvs_fluct[pvname]
            fluct = sigma * _np.random.randn()
            return value + fluct

    def update_timestamp(self):
        self._timestamp = _time.time()

    def times_up(self):
        if _time.time() > self._timestamp + self._interval:
            return True
        else:
            return False

    def _add_pvs_fluctuation(self, pvdb, pvsfluct):
        pvs_value = dict()
        pvs_fluct = dict()
        for pattern, fluct in pvsfluct.items():
            regexp = _re.compile(pattern)   
            for pvname, db in pvdb.items():
                if regexp.match(pvname):
                    pvs_value[pvname] = db['value']
                    pvs_fluct[pvname] = fluct
        return pvs_value, pvs_fluct
