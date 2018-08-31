"""Module to deal with correctors."""

from functools import partial as _part
from threading import Thread as _Thread
import siriuspy.csdevice.orbitcorr as _csorb
import siriuspy.csdevice.timesys as _cstime
from siriuspy.search.hl_time_search import HLTimeSearch as _HLTimeSearch
from siriuspy.csdevice.pwrsupply import Const as _PwrSplyConst
from siriuspy.callbacks import Callback as _Callback

TIMEOUT = 0.05


class RFCtrl(_Callback):

    def get_database(self):
        db = {
            'Freq-SP': {
                'type': 'float', 'value': 0, 'fun_set_pv': self.set_freq},
            'Freq-RB': {'type': 'float', 'value': 0},
            'PwrState-Sel': {
                'type': 'enum', 'enums': _PwrSplyConst.PwrState._fields,
                'value': 0, 'fun_set_pv': self.set_pwrstate},
            'PwrState-Sts': {
                'type': 'enum', 'enums': _PwrSplyConst.PwrState._fields,
                'value': 0},
        }
        return {self._name+':'+k: v for k, v in db.items()}

    def __init__(self, idx, ioc_callback=None, orb_callback=None):
        super().__init__()
        self._name = _csorb.RF_GEN_NAME
        self._idx = idx
        self._sp = 0
        self._rb = 0
        self._pwrstt = _PwrSplyConst.PwrState.Off
        self.add_callback(ioc_callback)
        self.add_callback(orb_callback)

    @property
    def value(self):
        return self._rb

    @value.setter
    def value(self, value):
        delta = value - self._rb
        self._sp = value
        self._rb = value
        self.run_callback(0, self._name+':Freq-RB', value)
        self.run_callback(1, self._idx, delta)

    @property
    def pwr_state(self):
        return self._pwrstt

    @pwr_state.setter
    def pwr_state(self, value):
        self._pwrstt = value
        self.run_callback(0, self._name+':PwrState-Sts', value)
        if self._pwrstt == _PwrSplyConst.PwrState.Off:
            self.value = 0.0
            self.run_callback(0, self._name+':Freq-SP', 0.0)

    def set_freq(self, value):
        if self._pwrstt == _PwrSplyConst.PwrState.Off:
            return False
        self.value = value
        return True

    def set_pwrstate(self, value):
        self.pwr_state = value
        return True


class CHCV(_Callback):

    def get_database(self):
        db = {
            'Current-SP': {
                'type': 'float', 'value': 0, 'fun_set_pv': self.set_curr},
            'Current-RB': {'type': 'float', 'value': 0},
            'CurrentRef-Mon': {'type': 'float', 'value': 0},
            'OpMode-Sel': {
                'type': 'enum', 'enums': _PwrSplyConst.OpMode._fields,
                'value': 0, 'fun_set_pv': self.set_opmode},
            'OpMode-Sts': {
                'type': 'enum', 'enums': _PwrSplyConst.OpMode._fields,
                'value': 0},
            'PwrState-Sel': {
                'type': 'enum', 'enums': _PwrSplyConst.PwrState._fields,
                'value': 0, 'fun_set_pv': self.set_pwrstate},
            'PwrState-Sts': {
                'type': 'enum', 'enums': _PwrSplyConst.PwrState._fields,
                'value': 0},
        }
        return {self._name+':'+k: v for k, v in db.items()}

    def __init__(self, idx, corr_name, ioc_callback=None, orb_callback=None):
        super().__init__()
        self._name = corr_name
        self._idx = idx
        self._sp = 0
        self._rb = 0
        self._ref = 0
        self._pwrstt = _PwrSplyConst.PwrState.Off
        self._opmode = _PwrSplyConst.OpMode.SlowRef
        self.add_callback(ioc_callback)
        self.add_callback(orb_callback)

    @property
    def value(self):
        return self._ref

    @value.setter
    def value(self, value):
        self._sp = value
        self._rb = value
        self.run_callback(0, self._name+':Current-RB', value)
        if self._opmode == _PwrSplyConst.OpMode.SlowRef:
            self.set_ref(True)

    @property
    def opmode(self):
        return self._opmode

    @opmode.setter
    def opmode(self, val):
        self._opmode = val
        self.run_callback(0, self._name+':OpMode-Sts', val)

    @property
    def pwr_state(self):
        return self._pwrstt

    @pwr_state.setter
    def pwr_state(self, value):
        self._pwrstt = value
        self.run_callback(0, self._name+':PwrState-Sts', value)
        if self._pwrstt == _PwrSplyConst.PwrState.Off:
            self.value = 0.0
            self.run_callback(0, self._name+':Current-SP', 0.0)
            self.set_ref(True)

    def set_ref(self, call_cb1=False):
        delta = self._sp - self._ref
        self._ref = self._sp
        self.run_callback(0, self._name+':CurrentRef-Mon', self._ref)
        if call_cb1:
            self.run_callback(1, self._idx, delta)

    def timing_trigger(self):
        if self._opmode == _PwrSplyConst.OpMode.SlowRefSync:
            self.set_ref(False)

    def set_curr(self, value):
        if self._pwrstt == _PwrSplyConst.PwrState.Off:
            return False
        self.value = value
        return True

    def set_opmode(self, value):
        if self._pwrstt == _PwrSplyConst.PwrState.Off:
            return False
        self.opmode = value
        return True

    def set_pwrstate(self, value):
        self.pwr_state = value
        return True


class Timing(_Callback):

    def get_database(self):
        db = _cstime.get_hl_event_database(prefix='')
        prop = 'fun_set_pv'
        db['Mode-Sel'][prop] = self.set_mode
        db['ExtTrig-Cmd'][prop] = self.set_trigger

        pref_name = _csorb.EVG_NAME + ':' + self._evt
        db = {pref_name+k: v for k, v in db.items()}

        db2 = _cstime.get_hl_trigger_database(self._trigger)
        for k, v in db2.items():
            if k.endswith(('-Sel', '-SP')):
                v[prop] = _part(self.set_trig_prop, k)
        db2 = {self._trigger+k: v for k, v in db2.items()}

        db.update(db2)
        return db

    def __init__(self, acc, ioc_callback, trig_callback):
        super().__init__()
        self._acc = acc
        self._evt = 'Orb' + acc.upper()
        self._trigger = acc.upper() + '-Glob:TI-Corrs:'
        srcs = _HLTimeSearch.get_hl_trigger_sources(self._trigger)
        self._trig_src_idx = srcs.index(self._evt)
        self.add_callback(ioc_callback)
        self.add_callback(trig_callback)

    def set_trig_prop(self, prop, value):
        pr = '_' + prop.split('-')[0].lower()
        setattr(self, pr, value)
        pr = prop.replace('-Sel', '-Sts').replace('-SP', '-RB')
        self.run_callback(0, self._trigger+pr, value)
        return True

    def set_mode(self, value):
        self._evt_mode = value
        self.run_callback(
            0, _csorb.EVG_NAME+':'+self._evt+'Mode-Sts', value)
        return True

    def set_trigger(self, value):
        if self._evt_mode == _cstime.events_modes.External:
            if self._trig_src_idx == self._src:
                self.run_callback(1)
        return True
