import time
import math
import datetime
from termcolor import colored

def timestamp_message(message, c1='yellow', a1=None, c2='white', a2=None):
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    if a1 is None: a1 = []
    if a2 is None: a2 = []
    return colored(st, c1, attrs=a1) + ': ' + colored(message, c2, attrs=a2)

class BeamCurrent:

    def __init__(self, current=0, lifetime = float("inf")):
        self._lifetime  = lifetime     # [hours]
        self._current   = current      # [a.u.]
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
        new_current = self._current * math.exp(-(t1-t0)/(60*60*self._lifetime))
        if math.isnan(new_current):
            new_current = self._current
        self._current = new_current
        # records timestamp and returns current value
        self._timestamp = t1
        return self._current

    def inject(self, delta_current):
        self._current = self.value + delta_current

    def dump(self):
        self._timestamp = time.time()
        self._current = 0
