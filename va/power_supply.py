
import math
import numpy as _np
from . import magnet
import siriuspy
from siriuspy.pwrsupply.model import PowerSupply as _PowerSupply
from siriuspy.csdevice.pwrsupply import default_wfmlabels as _default_wfmlabels


# These classes extend the base class PowerSupply in siriuspy


class PowerSupply(_PowerSupply):

    def __init__(self, magnets, model, name_ps):
        """Gets and sets current [A]
        Connected magnets are processed after current is set.
        """
        super().__init__(name_ps=name_ps)
        self._model = model
        self._magnets = magnets
        self._interlock = 0
        for m in magnets:
            m.add_power_supply(self)

    @property
    def interlock(self):
        # This will eventually be implemented in _PowerSupply!
        return self._interlock

    def process(self):
        for m in self._magnets:
            m.process()

    def get_pv(self, pv_name, parts):
        if parts.propty.endswith('Current-SP'): return self.current_sp
        if parts.propty.endswith('Current-RB'): return self.current_rb
        if parts.propty.endswith('CurrentRef-Mon'): return self.currentref_mon
        if parts.propty.endswith('Current-Mon'): return self.current_mon
        if parts.propty.endswith('PwrState-Sel'): return self.pwrstate_sts
        if parts.propty.endswith('PwrState-Sts'): return self.pwrstate_sts
        if parts.propty.endswith('OpMode-Sel'): return self.opmode_sel
        if parts.propty.endswith('OpMode-Sts'): return self.opmode_sts
        if parts.propty.endswith('CtrlMode-Mon'): return self.ctrlmode_mon
        if parts.propty.endswith('Reset-Cmd'): return 0
        if parts.propty.endswith('Interlock-SP'): return self.interlock
        if parts.propty.endswith('WfmIndex-Mon'): return self.wfmindex_mon
        if parts.propty.endswith('WfmLabels-Mon'): return self.wfmlabels_mon
        if parts.propty.endswith('WfmLabel-SP'): return self.wfmlabel_sp
        if parts.propty.endswith('WfmLabel-RB'): return self.wfmlabel_rb
        if parts.propty.endswith('WfmData-SP'): return self.wfmdata_sp
        if parts.propty.endswith('WfmData-RB'): return self.wfmdata_rb
        if parts.propty.endswith('WfmSave-Cmd'): return self.wfmsave_cmd
        if parts.propty.endswith('WfmLoad-Sel'): return self.wfmload_sel
        if parts.propty.endswith('WfmLoad-Sts'): return self.wfmload_sts
        if parts.propty.endswith('WfmRamping-Mon'): return self.wfmramping_mon
        return None

    def set_pv(self, pv_name, value, parts):
        propty = parts.propty
        deprecated_pvs = {}
        if propty.endswith('Current-SP'):
            prev_value = self.current_rb
            if value != prev_value:
                self.current_sp = value
                deprecated_pvs[pv_name] = self.current_sp
                deprecated_pvs[pv_name.replace('-SP','-RB')] = self.current_rb
                deprecated_pvs[pv_name.replace('Current-SP','CurrentRef-Mon')] = self.currentref_mon
                deprecated_pvs[pv_name.replace('-SP','-Mon')] = self.current_mon
        elif propty.endswith('PwrState-Sel'):
            prev_value = self.pwrstate_sts
            if value != prev_value:
                self.pwrstate_sel = value
                deprecated_pvs[pv_name.replace('-Sel','-Sts')] = self.pwrstate_sts
                deprecated_pvs[pv_name.replace('PwrState-Sel','CurrentRef-Mon')] = self.currentref_mon
                deprecated_pvs[pv_name.replace('PwrState-Sel','Current-Mon')] = self.current_mon
        elif propty.endswith('OpMode-Sel'):
            prev_value = self.opmode_sts
            if value != prev_value:
                self.opmode_sel = value
                deprecated_pvs[pv_name.replace('OpMode-Sel','OpMode-Sts')] = self.opmode_sts
        elif propty.endswith('WfmLabel-SP'):
            prev_value = self.wfmlabel_rb
            if value != prev_value:
                self.wfmlabel_sp = value
                deprecated_pvs[pv_name.replace('-SP','-RB')] = self.wfmlabel_rb
        elif propty.endswith('WfmData-SP'):
            prev_value = self.wfmdata_sp
            if (value != prev_value).any():
                self.wfmdata_sp = value
                deprecated_pvs[pv_name.replace('-SP','-RB')] = self.wfmdata_rb
        elif propty.endswith('WfmLoad-Sel'):
            prev_value = self.wfmload
            if value != prev_value:
                self.wfmload_sel = value
                deprecated_pvs[pv_name.replace('-Sel','-Sts')] = self.wfmload_sts
        elif propty.endswith('WfmSave-Cmd'):
            self.wfmsave_cmd = value
            deprecated_pvs[pv_name] = self.wfmsave_cmd
        if not deprecated_pvs:
            return False
        else:
            self.process()
            return deprecated_pvs

# class PowerSupply2(object):
#
#     def __init__(self, magnets, model, name_ps):
#         """Gets and sets current [A]
#         Connected magnets are processed after current is set.
#         """
#         self._model = model
#         self._name_ps = name_ps
#         self._magnets = magnets
#         self._pwrstate_sts = 1  # [On]
#         self.ctrlmode_mon = 0
#         self._current_sp = 0
#         self._current_rb = self._current_sp
#         self._currentref = self._current_rb
#         self._current_load = self._currentref
#         self._wfmindex = 0
#         self._wfmlabels = [label for label in _default_wfmlabels]
#         self._wfmslot = 0
#         self._waveform = siriuspy.pwrsupply.PSWaveForm.wfm_constant(self._wfmlabels[0])
#         self._opmode = 0
#         self._wfmramping = 0
#         self._interlock = 0
#         self._wfmsave = 0
#         for m in magnets:
#             m.add_power_supply(self)
#
#     @property
#     def interlock(self):
#         return self._interlock
#
#     @property
#     def current_sp(self):
#         return self._current_sp
#
#     @property
#     def current_rb(self):
#         return self._current_rb
#
#     @property
#     def current_load(self):
#         return self._current_load
#
#     @property
#     def currentref(self):
#         return self._currentref
#
#     @property
#     def pwrstate_sts(self):
#         return self._pwrstate_sts
#
#     @property
#     def wfmindex(self):
#         return self._wfmindex
#
#     @property
#     def wfmlabels(self):
#         return [label for label in self._wfmlabels]
#
#     @property
#     def wfmlabel(self):
#         return self._waveform.label
#
#     @property
#     def wfmdata(self):
#         return self._waveform.data
#
#     @wfmdata.setter
#     def wfmdata(self, value):
#         self._waveform.data = _np.array(value)
#
#     @wfmlabel.setter
#     def wfmlabel(self, value):
#         self._waveform.label = value
#
#     @property
#     def wfmsave(self):
#         return self._wfmsave
#
#     @wfmsave.setter
#     def wfmsave(self, value):
#         self._wfmsave += 1
#
#     @property
#     def wfmload(self):
#         return self._wfmslot
#
#     @property
#     def wfmramping(self):
#         return self._wfmramping
#
#     @wfmload.setter
#     def wfmload(self, value):
#         self._wfmslot = value
#         self._waveform = siriuspy.pwrsupply.PSWaveForm.wfm_constant(self._wfmlabels[0])
#
#     def _current_load_setter(self, value): # called only from within this class
#         self._current_rb = value
#         self._currentref = self._current_rb
#         self._current_load = self._currentref
#         for m in self._magnets:
#             m.process()
#
#     @current_sp.setter
#     def current_sp(self, value):
#         if self.ctrlmode_mon == 1: return # CtrlState: Local
#         self._current_sp = value
#         if self._pwrstate_sts and self.opmode == 0:
#             self._current_load_setter(value)
#
#     @pwrstate_sts.setter
#     def pwrstate_sts(self, value):
#         if self.ctrlmode_mon == 1: return # ctrlmode_mon: Local
#         self._pwrstate_sts = value
#         if value == 0:
#             self._current_load_setter(0)
#         else:
#             self._current_load_setter(self._current_sp)
#
#     @property
#     def opmode(self):
#         return self._opmode
#
#     @opmode.setter
#     def opmode(self, value):
#         if self.ctrlmode_mon == 1: return # ctrlmode_mon: Local
#         self._opmode = value


class FamilyPowerSupply(PowerSupply):

    def __init__(self, magnets, model, name_ps, current=None):
        """Initialises current from average integrated field in magnets"""
        super().__init__(magnets, model=model, name_ps=name_ps)
        if (current is None) and (len(magnets) > 0):
            total_current = 0.0
            n = 0
            for m in magnets:
                total_current += m.get_current_from_field()
                n += 1
            self.current_sp = total_current/n
        else:
            self.current_sp = 0.0


class IndividualPowerSupply(PowerSupply):

    def __init__(self, magnets, model, name_ps, current=None):
        super().__init__(magnets, model=model, name_ps=name_ps)
        if len(magnets) > 1:
            raise Exception('Individual Power Supply')
        elif (current is None) and (len(magnets) > 0):
            m = list(magnets)[0]
            total_current = m.get_current_from_field()
            power_supplies = m._power_supplies.difference({self})
            ps_current = 0.0
            for ps in power_supplies:
                ps_current += ps.current_mon
            self.current_sp = (total_current - ps_current) if math.fabs((total_current - ps_current))> 1e-10 else 0.0
        else:
            self.current_sp = 0.0


class PulsedMagnetPowerSupply(IndividualPowerSupply):

    def __init__(self, magnets, model, name_ps, current=None):
        super().__init__(magnets, model=model, name_ps=name_ps)
        if current is not None: self.current_sp = current

    @property
    def enabled(self):
        magnet = list(self._magnets)[0]
        if hasattr(magnet, 'enabled'):
            return magnet.enabled
        else:
            return True

    @property
    def magnet_idx(self):
        magnet = list(self._magnets)[0]
        idx = magnet.indices[0]
        return idx
