import time
import math
import datetime
from termcolor import colored

def timestamp_message(message, c1='yellow', a1=None, c2='white', a2=None):
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    if a1 is None: a1 = []
    if a2 is None: a2 = []
    return colored(st, c1, attrs=a1) + ': ' + colored(message, c2, attrs=a2)

class BeamCharge:

    def __init__(self, charge=0, lifetime = float("inf")):
        self._lifetime  = lifetime     # [seconds]
        self._charge    = charge       # [coulomb]
        self._timestamp = time.time()

    @property
    def lifetime(self):
        return self._lifetime

    @lifetime.setter
    def lifetime(self, value):
        self._lifetime = value

    @property
    def value(self):
        # updates current value
        t0, t1 = self._timestamp, time.time()
        new_charge = self._charge * math.exp(-(t1-t0)/self._lifetime)
        if math.isnan(new_charge):
            new_charge = self._charge
        self._charge = new_charge
        # records timestamp and returns current value
        self._timestamp = t1
        return self._charge

    def inject(self, delta_charge):
        self._charge = self.value + delta_charge

    def dump(self):
        self._timestamp = time.time()
        self._charge = 0
