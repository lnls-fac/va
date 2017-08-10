import pvs as _pvs
import time as _time
import random as _random
import epics as _epics
from siriuspy.envars import vaca_prefix

__version__ = _pvs.__version__


class App:

    NOISELVL = 100  # in nanometers
    PVS_PREFIX = vaca_prefix
    VA_PREFIX = 'fac' + vaca_prefix[8:]
    pvs_database = _pvs.pvs_database

    def __init__(self, driver):
        self._driver = driver
        self._my_pvs = dict()
        for pv_name in self.pvs_database.keys():
            if pv_name == 'Version':
                continue
            pv = _epics.PV(self.VA_PREFIX + pv_name)
            # pv.add_callback(self._onChanges)
            self._my_pvs[pv_name] = pv

    @property
    def driver(self):
        return self._driver

    def process(self, interval):
        start_time = _time.time()

        for pv_name, pv in self._my_pvs.items():
            value = pv.get()
            self._add_noise(pv_name, value)
        self._driver.updatePVs()

        delta_t = _time.time() - start_time
        if 0 < delta_t < interval:
            _time.sleep(interval - delta_t)

    def read(self, reason):
        return None

    def write(self, reason, value):
        return False

    def _add_noise(self, pv_name, value):
        if value is None:
            return
        if isinstance(value, (int, float)):
            value += self.NOISELVL * _random.uniform(-0.5, 0.5)
        else:
            for i in range(len(value)):
                value[i] += self.NOISELVL * _random.uniform(-0.5, 0.5)
        self._driver.setParam(pv_name, value)
