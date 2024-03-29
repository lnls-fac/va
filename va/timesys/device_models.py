"""Define Classes to simulate timing objects."""
import re as _re
import time as _time
import copy as _copy
import uuid as _uuid
from threading import Thread as _Thread

from siriuspy.timesys.csdev import Const

_OPT_SIM_TMP = 'IntTrig{0:02d}'
_OUT_SIM_TMP = 'OUT{0:d}'


class Callback:
    """Base Class for all Timing Simulation."""

    def __init__(self, callbacks=None, prefix=None):
        """Initialize the instance."""
        self.prefix = prefix or ''
        self._callbacks = dict(callbacks) if callbacks else dict()

    def _callback(self, propty, value, **kwargs):
        return NotImplemented

    def _call_callbacks(self, propty, value, **kwargs):
        for uuid, callback in self._callbacks.items():
            callback(self.prefix + propty, value, **kwargs)

    def add_callback(self, *args):
        """Add callbacks."""
        if len(args) < 2 and isinstance(args[0], dict):
            self._callbacks.update(args[0])
        elif len(args) == 2:
            uuid, callback = args
            self._callbacks[uuid] = callback
        else:
            raise Exception('wrong input for add_callback')

    def remove_callback(self, uuid):
        """Remove callbacks."""
        self._callbacks.pop(uuid)


class _BaseSim(Callback):

    _attributes = {}

    def __init__(self, callbacks=None):
        super().__init__(callbacks)

    def __getattr__(self, name):
        if name in self.__class__._attributes:
            return self.__dict__['_'+name]
        else:
            return super().__getattr__(name)

    def __setattr__(self, name, value):
        if name in self.__class__._attributes:
            self.__dict__['_'+name] = value
            self._call_callbacks(name, value)
        else:
            super().__setattr__(name, value)


class _BaseIOC(Callback):

    @classmethod
    def get_database(cls, prefix=''):
        return NotImplemented  # return db

    def __init__(self, control, callbacks=None, prefix=None):
        super().__init__(callbacks, prefix=prefix)
        self.uuid = _uuid.uuid4()
        self._pvname2attr = {
            value: key for key, value in self._attr2pvname.items()}
        self._control = control
        self._control.add_callback({self.uuid: self._callback})
        self.base_freq = self._control.base_freq
        self._set_init_values()

    def __getattr__(self, name):
        if name in self.__class__._attr2pvname.keys():
            return self.__dict__['_'+name]
        else:
            raise AttributeError(
                self.__class__.__name__ +
                " object has no attribute '_" + name + "'")

    def __setattr__(self, name, value):
        if name in self.__class__._attr2pvname.keys():
            f_ = self._attr2expr.get(name)
            pvalue = f_(value)
            if name.endswith(('_sp', '_sel')):
                self._control.__setattr__(name[:-3], pvalue)
                self.__dict__['_'+name] = value
            elif name.endswith(('_rb', '_sts')):
                self.__dict__['_'+name] = pvalue
                self._call_callbacks(self._attr2pvname[name], pvalue)
            elif name.endswith(('_cmd',)):
                self.__dict__['_'+name] = pvalue
        else:
            super().__setattr__(name, value)

    @property
    def control(self):
        return self._control

    def _set_init_values(self):
        db = self.get_database()
        for attr, pv in self._attr2pvname.items():
            self.__setattr__('_' + attr, db[pv]['value'])

    def get_propty(self, reason):
        reason = reason[len(self.prefix):]
        if reason not in self._pvname2attr.keys():
            return None
        return self.__getattr__(self._pvname2attr[reason])

    def set_propty(self, reason, value):
        reason = reason[len(self.prefix):]
        if reason not in self._pvname2attr.keys() or \
                reason.endswith(('-RB', '-Sts')):
            return False
        self.__setattr__(self._pvname2attr[reason], value)
        return True


# #############################################################
# ############# Event Generator Part ##########################
# #############################################################

class _ClockSim(_BaseSim):

    _attributes = {'state', 'frequency'}

    def __init__(self, base_freq, callbacks=None):
        super().__init__(callbacks)
        self.base_freq = base_freq
        self._frequency = 1
        self._state = 0

    def generate(self):
        if self._state > 0:
            return {'frequency': self.base_freq/self._frequency}


class _EventSim(_BaseSim):

    _attributes = {'delay', 'mode', 'delay_type', }

    def __init__(self, base_freq, callbacks=None):
        super().__init__(callbacks)
        self.base_freq = base_freq
        self._delay_type = 0
        self._delay = 0
        self._mode = 0

    def generate(self):
        if self._mode > 0:
            return {'delay': self._delay/self.base_freq}


class _EVGSim(_BaseSim):

    _attributes = {
        'continuous', 'repeat_bucketlist', 'bucket_list', 'repetition_rate',
        'injection', 'statemachine'}

    def __init__(self, base_freq, callbacks=None):
        super().__init__(callbacks)
        self.base_freq = base_freq
        self._pending_devices_callbacks = dict()
        self._continuous = 1
        self._statemachine = 2
        self._injection = 0
        self._injection_callbacks = dict()
        self._repeat_bucketlist = 0
        self._bucket_list = [0.0]*864
        self._repetition_rate = 30
        self._rf_division = 4
        self.events = list()
        for _ in Const.EvtLL:
            self.events.append(_EventSim(self.base_freq/self._rf_division))
        self.eventshl = list()
        for i in range(len(Const.EvtLL2HLMap)):
            self.eventshl.append(self.events[i])
        self.clocks = list()
        for _ in Const.ClkLL:
            self.clocks.append(_ClockSim(self.base_freq/self._rf_division))

    def __setattr__(self, attr, value):
        if attr == 'injection':
            if value:
                if not self._injection and self._continuous:
                    self._injection = value
                    _Thread(target=self._injection_fun).start()
            else:
                self._injection = value
            self._call_callbacks('injection', value)
        else:
            super().__setattr__(attr, value)

    def add_pending_devices_callback(self, uuid, callback):
        self._pending_devices_callbacks.update({uuid: callback})

    def remove_pending_devices_callback(self, uuid):
        self._pending_devices_callbacks.pop(uuid, None)

    # ########## Functions related to Single Pulse simulation #############
    def add_injection_callback(self, uuid, callback):
        self._injection_callbacks.update({uuid: callback})

    def remove_injection_callback(self, uuid):
        self._injection_callbacks.pop(uuid, None)

    def _injection_fun(self):
        repeat = self._repeat_bucketlist
        self._statemachine = 3
        self._call_callbacks('statemachine', 3)
        while True:
            if not len(self._bucket_list):
                _time.sleep(0.1)
            for i in self._bucket_list:
                if not self._can_inject():
                    return
                if i <= 0:
                    break
                evnts = self._generate_events((1, 2))
                triggers = dict()
                for callback in self._pending_devices_callbacks.values():
                    triggers.update(callback(i, evnts))
                for callback in self._injection_callbacks.values():
                    callback(i, triggers)
                _time.sleep(self._repetition_rate/Const.AC_FREQUENCY)
            if repeat == 1:
                self._injection = 0
                self._statemachine = 2
                self._call_callbacks('statemachine', 2)
                self._call_callbacks('injection', 0)
                return
            repeat -= 1

    def _can_inject(self):
        if not self._continuous or not self._injection:
            return False
        return True
    ######################################################################

    def _generate_events(self, tables):
        tables = tables if isinstance(tables, (list, tuple)) else (tables,)
        events = dict()
        for i, ev in enumerate(self.events):
            lab = Const.EvtLL._fields[i]
            if ev.mode not in tables:
                continue
            dic = ev.generate()
            if not dic:
                continue
            events.update({lab: dic})
        for i, cl in enumerate(self.clocks):
            dic = cl.generate()
            if not dic:
                continue
            lab = Const.ClkLL._fields[i]
            events.update({lab: dic})
        return events


class _EventIOC(_BaseIOC):

    _attr2pvname = {
        'delay_sp': 'Delay-SP',
        'delay_rb': 'Delay-RB',
        'mode_sp': 'Mode-Sel',
        'mode_rb': 'Mode-Sts',
        'delay_type_sp': 'DelayType-Sel',
        'delay_type_rb': 'DelayType-Sts',
        'exttrig_cmd': 'ExtTrig-Cmd'
        }

    @classmethod
    def get_database(cls, prefix=''):
        db = dict()
        dic_ = {'type': 'int', 'value': 0,
                'lolo': 0, 'low': 0, 'lolim': 0,
                'hilim': 2147483647, 'high': 2147483647, 'hihi': 2147483647}
        db[prefix + 'Delay-SP'] = _copy.deepcopy(dic_)
        db[prefix + 'Delay-RB'] = dic_
        db[prefix + 'Mode-Sel'] = {
            'type': 'enum', 'enums': Const.EvtModes._fields, 'value': 1}
        db[prefix + 'Mode-Sts'] = {
            'type': 'enum', 'enums': Const.EvtModes._fields, 'value': 1}
        db[prefix + 'DelayType-Sel'] = {
            'type': 'enum', 'enums': Const.EvtDlyTyp._fields, 'value': 1}
        db[prefix + 'DelayType-Sts'] = {
            'type': 'enum', 'enums': Const.EvtDlyTyp._fields, 'value': 1}
        db[prefix + 'ExtTrig-Cmd'] = {
            'type': 'int', 'value': 0}
        return db

    def __init__(self, base_freq, callbacks=None, prefix=None, control=None):
        self._attr2expr = {
            'delay_sp': lambda x: int(x),
            'delay_rb': lambda x: x,
            'mode_sp': lambda x: int(x),
            'mode_rb': lambda x: x,
            'delay_type_sp': lambda x: int(x),
            'delay_type_rb': lambda x: x,
            'exttrig_cmd': lambda x: x,
            }
        if control is None:
            control = _EventSim(base_freq)
        super().__init__(control, callbacks, prefix=prefix)

    def _callback(self, propty, value, **kwargs):
        if propty == 'delay':
            self.delay_rb = value
        if propty == 'mode':
            self.mode_rb = value
        if propty == 'delay_type':
            self.delay_type_rb = value


class _ClockIOC(_BaseIOC):

    _attr2pvname = {
        'frequency_sp': 'MuxDiv-SP',
        'frequency_rb': 'MuxDiv-RB',
        'state_sp': 'MuxEnbl-Sel',
        'state_rb': 'MuxEnbl-Sts',
        }

    @classmethod
    def get_database(cls, prefix=''):
        db = dict()
        dic_ = {'type': 'int', 'value': 124948114,
                'lolo': 1, 'low': 1, 'lolim': 1,
                'hilim': 4294967296, 'high': 4294967296, 'hihi': 4294967296}
        db[prefix + 'MuxDiv-SP'] = _copy.deepcopy(dic_)
        db[prefix + 'MuxDiv-RB'] = dic_
        db[prefix + 'MuxEnbl-Sel'] = {
            'type': 'enum', 'enums': Const.ClockStates._fields, 'value': 0}
        db[prefix + 'MuxEnbl-Sts'] = {
            'type': 'enum', 'enums': Const.ClockStates._fields, 'value': 0}
        return db

    def __init__(self, base_freq, callbacks=None, prefix=None, control=None):
        self._attr2expr = {
            'frequency_sp': lambda x: int(x),
            'frequency_rb': lambda x: x,
            'state_sp': lambda x: int(x),
            'state_rb': lambda x: x,
            }
        if control is None:
            control = _ClockSim(base_freq)
        super().__init__(control, callbacks, prefix=prefix)

    def _callback(self, propty, value, **kwargs):
        if propty == 'frequency':
            self.frequency_rb = value
        if propty == 'state':
            self.state_rb = value


class EVGIOC(_BaseIOC):
    """Class to Simulate the EVG."""

    _states = ('Dsbl', 'Enbl')
    _cyclic_types = ('Off', 'On')

    _attr2pvname = {
        'injection_sp': 'InjectionEvt-Sel',
        'injection_rb': 'InjectionEvt-Sts',
        'repeat_bucketlist_sp': 'RepeatBucketList-SP',
        'repeat_bucketlist_rb': 'RepeatBucketList-RB',
        'statemachine': 'STATEMACHINE',
        'continuous_sp': 'ContinuousEvt-Sel',
        'continuous_rb': 'ContinuousEvt-Sts',
        'repetition_rate_sp': 'ACDiv-SP',
        'repetition_rate_rb': 'ACDiv-RB',
        'rf_division_sp': 'RFDiv-SP',
        'rf_division_rb': 'RFDiv-RB',
        'bucket_list_sp': 'BucketList-SP',
        'bucket_list_rb': 'BucketList-RB',
        }

    @classmethod
    def get_database(cls, prefix=''):
        """Get the database."""
        db = dict()
        p = prefix
        db[p + 'InjectionEvt-Sel'] = {
            'type': 'enum', 'enums': Const.DsblEnbl._fields, 'value': 0}
        db[p + 'InjectionEvt-Sts'] = {
            'type': 'enum', 'enums': Const.DsblEnbl._fields, 'value': 0}
        db[p + 'RepeatBucketList-SP'] = {
            'type': 'int', 'value': 0, 'lolo': 0, 'low': 0, 'lolim': 0,
            'hilim': 100, 'high': 100, 'hihi': 100}
        db[p + 'RepeatBucketList-RB'] = {
            'type': 'int', 'value': 0, 'lolo': 0, 'low': 0, 'lolim': 0,
            'hilim': 100, 'high': 100, 'hihi': 100}
        db[p + 'STATEMACHINE'] = {
            'type': 'int', 'value': 2, 'lolo': 0, 'low': 0, 'lolim': 0,
            'hilim': 6, 'high': 6, 'hihi': 6}
        db[p + 'ContinuousEvt-Sel'] = {
            'type': 'enum', 'enums': Const.DsblEnbl._fields, 'value': 1}
        db[p + 'ContinuousEvt-Sts'] = {
            'type': 'enum', 'enums': Const.DsblEnbl._fields, 'value': 1}
        db[p + 'BucketList-SP'] = {
            'type': 'int', 'count': 864, 'value': 864*[0]}
        db[p + 'BucketList-RB'] = {
            'type': 'int', 'count': 864, 'value': 864*[0]}
        dic_ = {'type': 'int', 'value': 30,
                'lolo': 1, 'low': 1, 'lolim': 1,
                'hilim': 60, 'high': 60, 'hihi': 60}
        db[p + 'ACDiv-SP'] = _copy.deepcopy(dic_)
        db[p + 'ACDiv-RB'] = dic_
        dic_ = {'type': 'int', 'value': 4,
                'lolo': 1, 'low': 1, 'lolim': 1,
                'hilim': 10, 'high': 20, 'hihi': 20}
        db[p + 'RFDiv-SP'] = _copy.deepcopy(dic_)
        db[p + 'RFDiv-RB'] = dic_
        for clc in Const.ClkLL._fields:
            p = prefix + clc
            db.update(_ClockIOC.get_database(p))
        for ev in Const.EvtLL._fields:
            p = prefix + ev
            db.update(_EventIOC.get_database(p))
        for ev in Const.EvtHL2LLMap.keys():
            p = prefix + ev
            db.update(_EventIOC.get_database(p))

        return db

    def __init__(self, base_freq, callbacks=None, prefix=None, control=None):
        """Initialize instance."""
        self._attr2expr = {
            'injection_sp': lambda x: int(x),
            'injection_rb': lambda x: x,
            'repeat_bucketlist_sp': lambda x: int(x),
            'repeat_bucketlist_rb': lambda x: x,
            'statemachine': lambda x: x,
            'continuous_sp': lambda x: int(x),
            'continuous_rb': lambda x: x,
            'repetition_rate_sp': lambda x: int(x),
            'repetition_rate_rb': lambda x: x,
            'rf_division_sp': lambda x: int(x),
            'rf_division_rb': lambda x: x,
            'bucket_list_sp': self._bucket_list_setter,
            'bucket_list_rb': lambda x: x,
            }
        if control is None:
            control = _EVGSim(base_freq)
        super().__init__(control, callbacks=callbacks, prefix=prefix)

        self.events = dict()
        for i, ev in enumerate(Const.EvtLL._fields):
            cntler = self.control.events[i]
            self.events[ev] = _EventIOC(
                self.base_freq/self._control._rf_division,
                callbacks={self.uuid: self._ioc_callback},
                prefix=ev,
                control=cntler)
        self.eventshl = dict()
        for evl, evh in Const.EvtLL2HLMap.items():
            self.eventshl[evh] = _EventIOC(
                self.base_freq/self._control._rf_division,
                callbacks={self.uuid: self._ioc_callback},
                prefix=evh,
                control=self.events[evl].control)
        self.clocks = dict()
        for i, clc in enumerate(Const.ClkLL._fields):
            cntler = self.control.clocks[i]
            self.clocks[clc] = _ClockIOC(
                self.base_freq/self._control._rf_division,
                callbacks={self.uuid: self._ioc_callback},
                prefix=clc,
                control=cntler)

    def _bucket_list_setter(self, value):
        bucket = []
        if isinstance(value, (int, float, str)):
            value = [value]
        for i in range(min(len(value), 864)):
            if value[i] <= 0:
                break
            bucket.append(int((value[i]-1) % 864) + 1)
        return bucket + (864-len(bucket)) * [0]

    def _ioc_callback(self, propty, value, **kwargs):
        self._call_callbacks(propty, value, **kwargs)

    def _callback(self, propty, value, **kwargs):
        if propty == 'continuous':
            self.continuous_rb = value
        elif propty == 'repeat_bucketlist':
            self.repeat_bucketlist_rb = value
        elif propty == 'bucket_list':
            self.bucket_list_rb = value
        elif propty == 'repetition_rate':
            self.repetition_rate_rb = value
        elif propty == 'rf_division':
            self.rf_division_rb = value
        elif propty == 'injection':
            self.injection_rb = value
            if value != self._injection_sp:
                self._injection_sp = value
                self._call_callbacks('InjectionEvt-Sel', value)

    def add_injection_callback(self, uuid, callback):
        """Add injection callback."""
        self._control.add_injection_callback(uuid, callback)

    def remove_injection_callback(self, uuid):
        """Remove injection callback."""
        self._control.remove_injection_callback(uuid)

    def add_pending_devices_callback(self, uuid, callback):
        """Add pending devices callback."""
        self._control.add_pending_devices_callback(uuid, callback)

    def remove_pending_devices_callback(self, uuid):
        """Remove pending devices callback."""
        self._control.remove_pending_devices_callback(uuid)

    def get_propty(self, reason):
        """Get propty."""
        reason2 = reason[len(self.prefix):]
        if reason2.startswith(tuple(self.clocks.keys())):
            reason3 = _re.findall('(Clk[0-7]{1}).*', reason2)[0]
            return self.clocks[reason3].get_propty(reason2)
        elif reason2.startswith(tuple(self.events.keys())):
            reason3 = _re.findall('(Evt[0-9]{2,3}).*', reason2)[0]
            return self.events[reason3].get_propty(reason2)
        elif reason2.startswith(tuple(self.eventshl.keys())):
            patt = '(' + '|'.join(tuple(self.eventshl.keys())) + ').*'
            reason3 = _re.findall(patt, reason2)[0]
            return self.eventshl[reason3].get_propty(reason2)
        else:
            return super().get_propty(reason)

    def set_propty(self, reason, value):
        """Set propty."""
        reason2 = reason[len(self.prefix):]
        if reason2.startswith(tuple(self.clocks.keys())):
            reason3 = _re.findall('(Clk[0-7]{1}).*', reason2)[0]
            return self.clocks[reason3].set_propty(reason2, value)
        elif reason2.startswith(tuple(self.events.keys())):
            reason3 = _re.findall('(Evt[0-9]{2,3}).*', reason2)[0]
            return self.events[reason3].set_propty(reason2, value)
        elif reason2.startswith(tuple(self.eventshl.keys())):
            patt = '(' + '|'.join(tuple(self.eventshl.keys())) + ').*'
            reason3 = _re.findall(patt, reason2)[0]
            return self.eventshl[reason3].set_propty(reason2, value)
        else:
            return super().set_propty(reason, value)


# #############################################################
# ############# Event Receivers Part ##########################
# #############################################################
class _OutputSim(_BaseSim):

    _attributes = {'fine_delay', 'delay', 'optic_channel'}

    def __init__(self, base_freq, callbacks=None):
        super().__init__(callbacks)
        self.base_freq = base_freq
        self._optic_channel = 'OTP00'
        self._delay = 0
        self._fine_delay = 0

    def receive_events(self, bucket, opts):
        dic = opts.get(self._optic_channel, None)
        if dic is None:
            return
        dic['delay'] += (
            self._delay/self.base_freq + self._fine_delay * Const.FINE_DELAY)
        return dic


class _InternTrigSim(_BaseSim):

    _attributes = {'state', 'width', 'delay', 'polarity', 'event', 'pulses'}

    def __init__(self, base_freq, callbacks=None):
        super().__init__(callbacks)
        self.base_freq = base_freq
        self._state = 0
        self._width = 0
        self._delay = 0
        self._polarity = 0
        self._event = 1
        self._pulses = 1

    def receive_events(self, bucket, events):
        if self._state == 0:
            return
        ev = events.get(self._event, None)
        if ev is None:
            return
        delay = ev['delay'] + self._delay/self.base_freq
        return {
            'pulses': self._pulses,
            'width': self._width/self.base_freq,
            'delay': delay}


class _EVRSim(_BaseSim):
    _ClassOutSim = _OutputSim
    _NR_INTERNAL_OPT_CHANNELS = 24
    _NR_OPT_CHANNELS = 12
    _NR_OUT_CHANNELS = 8

    _attributes = {'state'}

    def __init__(self, base_freq, callbacks=None):
        super().__init__(callbacks)
        self.base_freq = base_freq
        self._state = 1

        self.internal_triggers = list()
        for _ in range(self._NR_INTERNAL_OPT_CHANNELS):
            self.internal_triggers.append(_InternTrigSim(self.base_freq))

        self.main_outputs = list()
        for _ in range(self._NR_OUT_CHANNELS):
            self.main_outputs.append(self._ClassOutSim(self.base_freq))

    def receive_events(self, bucket, events):
        triggers = dict()
        inp_dic = dict(events)
        for i, opt_ch in enumerate(self.internal_triggers):
            opt = opt_ch.receive_events(bucket, inp_dic)
            if opt is None:
                continue
            lab = _OPT_SIM_TMP.format(i)
            inp_dic.update({lab: opt})
            if i < self._NR_OPT_CHANNELS:
                triggers.update({lab: opt})
        for tri_ch in self.main_outputs:
            out = tri_ch.receive_events(bucket, inp_dic)
            if out is None:
                continue
            lab = _OUT_SIM_TMP.format(i)
            triggers.update({lab: out})
        return triggers


class _EVESim(_EVRSim):
    _ClassOutSim = _OutputSim
    _NR_INTERNAL_OPT_CHANNELS = 24
    _NR_OPT_CHANNELS = 0
    _NR_OUT_CHANNELS = 8


class _AFCSim(_EVRSim):
    _ClassOutSim = _InternTrigSim
    _NR_INTERNAL_OPT_CHANNELS = 10
    _NR_OPT_CHANNELS = 10
    _NR_OUT_CHANNELS = 8


class _EVROutputIOC(_BaseIOC):

    _attr2pvname = {
        'fine_delay_sp':    'FineDelay-SP',
        'fine_delay_rb':    'FineDelay-RB',
        'delay_sp':         'RFDelay-SP',
        'delay_rb':         'RFDelay-RB',
        'optic_channel_sp': 'IntChan-Sel',
        'optic_channel_rb': 'IntChan-Sts',
        }

    _int_chan_enums = ['OTP{0:02d}'.format(i) for i in range(24)]
    _int_chan_enums += Const.ClkLL._fields

    @classmethod
    def get_database(cls, prefix=''):
        db = dict()
        dic_ = {
            'type': 'int', 'value': 0, 'lolo': 0, 'low': 0, 'lolim': 0,
            'hilim': 200, 'high': 200, 'hihi': 200}
        db[prefix + 'FineDelay-SP'] = _copy.deepcopy(dic_)
        db[prefix + 'FineDelay-RB'] = dic_

        dic_ = {
            'type': 'int', 'value': 0, 'lolo': 0, 'low': 0, 'lolim': 0,
            'hilim': 30, 'high': 31, 'hihi': 31}
        db[prefix + 'RFDelay-SP'] = _copy.deepcopy(dic_)
        db[prefix + 'RFDelay-RB'] = dic_

        db[prefix + 'IntChan-Sel'] = {
            'type': 'string', 'value': 'IntTrig00',
            'Enums': cls._int_chan_enums}
        db[prefix + 'IntChan-Sts'] = {
            'type': 'string', 'value': 'IntTrig00',
            'Enums': cls._int_chan_enums}
        return db

    def __init__(self, base_freq, callbacks=None, prefix=None, control=None):
        self._attr2expr = {
            'fine_delay_sp': lambda x: int(x),
            'fine_delay_rb': lambda x: x,
            'delay_sp': lambda x: int(x),
            'delay_rb': lambda x: x,
            'optic_channel_sp': lambda x: x,
            'optic_channel_rb': lambda x: x,
            }
        if control is None:
            control = _OutputSim(base_freq)
        super().__init__(control, callbacks, prefix=prefix)

    def _callback(self, propty, value, **kwargs):
        if propty == 'delay':
            self.delay_rb = value
        if propty == 'fine_delay':
            self.fine_delay_rb = value
        if propty == 'optic_channel':
            self.optic_channel_rb = value


class _EVEOutputIOC(_EVROutputIOC):

    _int_chan_enums = ['OTP{0:02d}'.format(i) for i in range(16)]
    _int_chan_enums += Const.ClkLL._fields


class _InternTrigIOC(_BaseIOC):

    _attr2pvname = {
        'state_sp': 'State-Sel',
        'state_rb': 'State-Sts',
        'width_sp': 'WidthRaw-SP',
        'width_rb': 'WidthRaw-RB',
        'delay_sp': 'DelayRaw-SP',
        'delay_rb': 'DelayRaw-RB',
        'polarity_sp': 'Polarity-Sel',
        'polarity_rb': 'Polarity-Sts',
        'event_sp': 'Evt-SP',
        'event_rb': 'Evt-RB',
        'pulses_sp': 'NrPulses-SP',
        'pulses_rb': 'NrPulses-RB',
        }

    @classmethod
    def get_database(cls, prefix=''):
        db = dict()
        db[prefix + 'State-Sel'] = {
            'type': 'enum', 'enums': Const.TrigStates._fields, 'value': 0}
        db[prefix + 'State-Sts'] = {
            'type': 'enum', 'enums': Const.TrigStates._fields, 'value': 0}

        dic_ = {
            'type': 'int', 'value': 1, 'lolo': 1, 'low': 1, 'lolim': 1,
            'hilim': 2147483647, 'high': 2147483647, 'hihi': 2147483647}
        db[prefix + 'WidthRaw-SP'] = _copy.deepcopy(dic_)
        db[prefix + 'WidthRaw-RB'] = dic_

        dic_ = {
            'type': 'int', 'value': 0, 'lolo': 0, 'low': 0, 'lolim': 0,
            'hilim': 2147483647, 'high': 2147483647, 'hihi': 2147483647}
        db[prefix + 'DelayRaw-SP'] = _copy.deepcopy(dic_)
        db[prefix + 'DelayRaw-RB'] = dic_
        db[prefix + 'Polarity-Sel'] = {
            'type': 'enum', 'enums': Const.TrigPol._fields, 'value': 0}
        db[prefix + 'Polarity-Sts'] = {
            'type': 'enum', 'enums': Const.TrigPol._fields, 'value': 0}
        db[prefix + 'Evt-SP'] = {
            'type': 'int', 'value': 1, 'lolo': 0, 'low': 0, 'lolim': 0,
            'hilim': 255, 'high': 255, 'hihi': 255}
        db[prefix + 'Evt-RB'] = {
            'type': 'int', 'value': 1, 'lolo': 0, 'low': 0, 'lolim': 0,
            'hilim': 255, 'high': 255, 'hihi': 255}

        dic_ = {
            'type': 'int', 'unit': 'numer of pulses', 'value': 1,
            'lolo': 1, 'low': 1, 'lolim': 1,
            'hilim': 2147483647, 'high': 2147483647, 'hihi': 2147483647}
        db[prefix + 'NrPulses-SP'] = _copy.deepcopy(dic_)
        db[prefix + 'NrPulses-RB'] = dic_
        return db

    def __init__(self, base_freq, callbacks=None, prefix=None, control=None):
        self._attr2expr = {
            'state_sp': lambda x: int(x),
            'state_rb': lambda x: x,
            'width_sp': lambda x: int(x),
            'width_rb': lambda x: x,
            'delay_sp': lambda x: int(x),
            'delay_rb': lambda x: x,
            'polarity_sp': lambda x: int(x),
            'polarity_rb': lambda x: x,
            'event_sp': lambda x: int(x),
            'event_rb': lambda x: x,
            'pulses_sp': lambda x: int(x),
            'pulses_rb': lambda x: x,
            }
        if control is None:
            control = _InternTrigSim(base_freq)
        super().__init__(control, callbacks, prefix=prefix)

    def _callback(self, propty, value, **kwargs):
        if propty == 'state':
            self.state_rb = value
        if propty == 'width':
            self.width_rb = value
        if propty == 'delay':
            self.delay_rb = value
        if propty == 'polarity':
            self.polarity_rb = value
        if propty == 'event':
            self.event_rb = value
        if propty == 'pulses':
            self.pulses_rb = value


class EVRIOC(_BaseIOC):
    """Class to simulate the EVR."""

    _ClassSim = _EVRSim
    _ClassOutIOC = _EVROutputIOC
    _ClassIntTrigIOC = _InternTrigIOC
    _OUTTMP = 'OUT{0:d}'
    _INTTMP = 'OTP{0:02d}'

    _attr2pvname = {
        'state_sp': 'DevEnbl-Sel',
        'state_rb': 'DevEnbl-Sts',
        }

    @classmethod
    def get_database(cls, prefix=''):
        """Get the database."""
        db = dict()
        p = prefix
        db[p + 'DevEnbl-Sel'] = {
            'type': 'enum', 'enums': Const.OffOn._fields, 'value': 0}
        db[p + 'DevEnbl-Sts'] = {
            'type': 'enum', 'enums': Const.OffOn._fields, 'value': 0}
        for i in range(cls._ClassSim._NR_INTERNAL_OPT_CHANNELS):
            p = prefix + cls._INTTMP.format(i)
            db.update(cls._ClassIntTrigIOC.get_database(p))
        for out in range(cls._ClassSim._NR_OUT_CHANNELS):
            p = prefix + cls._OUTTMP.format(out)
            db.update(cls._ClassOutIOC.get_database(p))
        return db

    def __init__(self, base_freq, callbacks=None, prefix=None, control=None):
        """Initialize the instance."""
        self._attr2expr = {
            'state_sp': lambda x: int(x),
            'state_rb': lambda x: x,
            }
        if control is None:
            control = self._ClassSim(base_freq)
        super().__init__(control, callbacks=callbacks, prefix=prefix)

        self.internal_triggers = dict()
        for i in range(self._ClassSim._NR_INTERNAL_OPT_CHANNELS):
            name = self._INTTMP.format(i)
            cntler = self._control.internal_triggers[i]
            self.internal_triggers[name] = self._ClassIntTrigIOC(
                self.base_freq,
                callbacks={self.uuid: self._ioc_callback},
                prefix=name,
                control=cntler)
        self.main_outputs = dict()
        for i in range(self._ClassSim._NR_OUT_CHANNELS):
            name = self._OUTTMP.format(i)
            cntler = self._control.main_outputs[i]
            self.main_outputs[name] = self._ClassOutIOC(
                self.base_freq,
                callbacks={self.uuid: self._ioc_callback},
                prefix=name,
                control=cntler)

    def _ioc_callback(self, propty, value, **kwargs):
        self._call_callbacks(propty, value, **kwargs)

    def _callback(self, propty, value, **kwargs):
        if propty == 'state':
            self.state_rb = value

    def get_propty(self, reason):
        """Get properties by PV name."""
        reason2 = reason[len(self.prefix):]
        if reason2.startswith(tuple(self.main_outputs.keys())):
            leng = len(self._OUTTMP.format(0))
            # Not general enough
            return self.main_outputs[reason2[: leng]].get_propty(reason2)
        elif reason2.startswith(tuple(self.internal_triggers.keys())):
            leng = len(self._INTTMP.format(0))
            # Absolutely not general enough
            return self.internal_triggers[reason2[: leng]].get_propty(reason2)
        else:
            return super().get_propty(reason)

    def set_propty(self, reason, value):
        """Set properties by PV name."""
        reason2 = reason[len(self.prefix):]
        if reason2.startswith(tuple(self.main_outputs.keys())):
            leng = len(self._OUTTMP.format(0))
            return self.main_outputs[reason2[:leng]].set_propty(
                reason2, value)
        elif reason2.startswith(tuple(self.internal_triggers.keys())):
            leng = len(self._INTTMP.format(0))
            return self.internal_triggers[reason2[:leng]].set_propty(
                reason2, value)
        else:
            return super().set_propty(reason, value)

    def receive_events(self, bucket, events):
        """Receive the events from the EVG."""
        return {self.prefix: self._control.receive_events(bucket, events)}


class EVEIOC(EVRIOC):
    """Class to simulate the EVE."""

    _ClassSim = _EVESim
    _ClassOutIOC = _EVEOutputIOC


class _AFCTrigIOC(_InternTrigIOC):

    _event_enums = Const.EvtLL._fields + Const.ClkLL._fields
    _attr2pvname = {
        'state_sp': 'State-Sel',
        'state_rb': 'State-Sts',
        'width_sp': 'WidthRaw-SP',
        'width_rb': 'WidthRaw-RB',
        'delay_sp': 'DelayRaw-SP',
        'delay_rb': 'DelayRaw-RB',
        'polarity_sp': 'Polarity-Sel',
        'polarity_rb': 'Polarity-Sts',
        'event_sp': 'Evt-SP',
        'event_rb': 'Evt-RB',
        'pulses_sp': 'NrPulses-SP',
        'pulses_rb': 'NrPulses-RB',
        }

    @classmethod
    def get_database(cls, prefix=''):
        db = super().get_database(prefix=prefix)
        return db


class AFCIOC(EVRIOC):
    """Class to simulate the AFC."""

    _ClassSim = _AFCSim
    _ClassOutIOC = _AFCTrigIOC
    _ClassIntTrigIOC = _AFCTrigIOC
    _OUTTMP = 'FMC{0:d}'
    _INTTMP = 'AMC{0:d}'
