import pvs as _pvs
import time as _time
import random as _random
import epics as _epics

# Coding guidelines:
# =================
# 01 - pay special attention to code readability
# 02 - simplify logic as much as possible
# 03 - unroll expressions in order to simplify code
# 04 - dont be afraid to generate simingly repeatitive flat code (they may be easier to read!)
# 05 - 'copy and paste' is your friend and it allows you to code 'repeatitive' (but clearer) sections fast.
# 06 - be consistent in coding style (variable naming, spacings, prefixes, suffixes, etc)

__version__ = _pvs.__version__

class App:
    NOISELVL = 100e-9
    PVS_PREFIX = ''
    VA_PREFIX = 'VA2-'
    pvs_database = _pvs.pvs_database

    def __init__(self,driver):
        self._driver = driver
        self._my_pvs = dict()
        for pv_name in self.pvs_database.keys():
            if pv_name == 'Version': continue
            print(pv_name)
            pv = _epics.PV(self.VA_PREFIX + pv_name)
            value = pv.get()
            # pv.add_callback(self._onChanges)
            self._my_pvs[pv_name] = pv
            self._driver.setParam(pv_name,value)
        self._driver.updatePVs()
        print(len(self._my_pvs),len(self.pvs_database))

    @property
    def driver(self):
        return self._driver

    def process(self,interval):
        start_time = _time.time()

        for pv_name, pv in self._my_pvs.items():
            value = pv.get()
            self._add_noise(pv_name, value)
        self._driver.updatePVs()

        delta_t = _time.time() - start_time
        if 0 < delta_t < interval:
            _time.sleep(interval - delta_t)

    def read(self,reason):
        return None

    def write(self,reason,value):
        return False # False: no write implemented.

    def _add_noise(self,pv_name, value):
        if value is None: return
        if isinstance(value,(int,float)):
            value += self.NOISELVL * _random.uniform(-0.5,0.5)
        else:
            for i in range(len(value)): value[i] += self.NOISELVL * _random.uniform(-0.5,0.5)
        self._driver.setParam(pv_name,value)

    # # Not used right now. It is usefull to add a callback to a pv when processing is not needed
    # def _onChanges(self,pvname=None,value=None, **kwargs):
    #     self._add_noise(pvname[4:], value)
    #     self._driver.updatePVs()
