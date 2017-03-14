import numpy as _np
import threading as _threading
import time as _time


class Event:
    def __init__(self,name,mode=None,delay_type=None):
        self.name = name
        self._mode = None
        self._modes = ('Dsbl','Cont','Inj','Sgl')
        self._delay_types = ('Fix','Incr')
        self._delay_type = None
        self._delay = 0
        self.mode = mode or 'Dsbl'
        self.delay_type = delay_type or 'Incr'

    @property
    def delay(self):
        return self._delay
    @delay.setter
    def delay(self,value):
        self._delay = (value // 8) * 8  #must respect steps of 8 ns

    @property
    def mode(self):
        return self._modes.index(self._mode)
    @mode.setter
    def mode(self,value):
        if value <len(self._modes):
            self._mode = self._modes[value]

    @property
    def delay_type(self):
        return self._delay_types.index(self._delay_type)
    @delay_type.setter
    def delay_type(self,value):
        if value <len(self._delay_types):
            self._delay_type = self._delay_types[value]


class Clock:
    def __init__(self,base_freq):
        self._base_frequency = base_freq
        self._frequency = self._base_frequency
        self._state = 'Enbl'
        self._states = ('Dsbl','Enbl')

    @property
    def state(self):
        return self._states.index(self._state)
    @state.setter
    def state(self,value):
        if value <len(self._states):
            self._state = self._states[value]

    @property
    def frequency(self):
        return self._frequency
    @frequency.setter
    def frequency(self,value):
        n = round(60/value)
        n = n if n<2^32 else 2^32
        self._frequency = self._base_frequency / n


class EVG:

    def __init__(self, frequency, events):
        self._frequency = frequency
        self._continuous = None
        self._cyclic_injection = None
        self._bucket_list = -1*_np.ones(864)
        self._repetition_rate = None
        self._injecting = False
        self.continuous = 'On'
        self._continuous_types = ('Off','On')
        self.cyclic_injection = 'Off'
        self.repetition_rate = 2
        self.events = dict()
        for ev in events:
            self.events[ev] = Event(ev,'Inj','Incr')
        self.clocks = dict()
        for i in range(8):
            self.clocks['Clck{0:d}'.format(i)] = Clock(self._frequency/4)

    @property
    def continuous(self):
        return self._continuous
    @continuous.setter
    def continuous(self,value):
        if value in ('Off','On'):
            self._continuous = value

    @property
    def cyclic_injection(self):
        return self._cyclic_injection
    @cyclic_injection.setter
    def cyclic_injection(self,value):
        if value in ('Off','On'):
            self._cyclic_injection = value

    @property
    def bucket_list(self):
        return self._bucket_list
    @bucket_list.setter
    def bucket_list(self,value):
        for i in range(min(len(value),864)):
            if value[i]<0: break
            self._bucket_list[i] = (value[i] % 864)
        self._bucket_list[i:] = -1

    @property
    def repetition_rate(self):
        return self._repetition_rate
    @repetition_rate.setter
    def repetition_rate(self,value):
        n = round(60/value)
        n = n if n<60 else 60
        self._repetition_rate = 60 / n

    def start_injection(self,callback):
        self._injecting = True
        threading.Thread(target=self._injection, kwargs={'callback':callback})

    def stop_injection(self):
        self._injecting = False

    def single_pulse(self,callback):
        if self.continuous == 'Off': return
        evnts = self._generate_events('Single')
        callback(evnts)

    ###function for internal use###
    def _injection(self, callback):
        while True:
            for i in self.bucket_list:
                if not self._can_inject(): return
                if i<0: break
                evnts = self._generate_events(('Inj','Cont'))
                callback(i,evnts)
                _time.sleep(1/self.repetition_rate)
            if self.cyclic_injection == 'Off':
                self._injecting = False
                break

    def _generate_events(tables):
        tables = tables if isinstance(tables,(list,tuple)) else (tables,)
        return [ev for ev in self._events.values() if ev.mode in tables]

    def _can_inject(self):
        if self.continuous == 'Off' or not self._injecting: return False
        return True
