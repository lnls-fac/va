
import math as _math
import numpy as _np
from siriuspy.pwrsupply.model import PowerSupply as _PowerSupply


# These classes extend the base class PowerSupply in siriuspy


class PowerSupply(_PowerSupply):

    def __init__(self, magnets, model, psname):
        """Gets and sets current [A]
        Connected magnets are processed after current is set.
        """
        super().__init__(psname=psname)
        self._model = model
        self._magnets = magnets
        for m in magnets:
            m.add_power_supply(self)


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
        if parts.propty.endswith('Reset-Cmd'): return self.reset
        if parts.propty.endswith('Abort-Cmd'): return self.abort
        if parts.propty.endswith('WfmIndex-Mon'): return self.wfmindex_mon
        if parts.propty.endswith('WfmLabels-Mon'): return self.wfmlabels_mon
        if parts.propty.endswith('WfmLabel-SP'): return self.wfmlabel_sp
        if parts.propty.endswith('WfmLabel-RB'): return self.wfmlabel_rb
        if parts.propty.endswith('WfmData-SP'): return self.wfmdata_sp
        if parts.propty.endswith('WfmData-RB'): return self.wfmdata_rb
        if parts.propty.endswith('WfmSave-Cmd'): return self.wfmsave_cmd
        if parts.propty.endswith('WfmLoad-Sel'): return self.wfmload_sel
        if parts.propty.endswith('WfmLoad-Sts'): return self.wfmload_sts
        if parts.propty.endswith('Intlk-Mon'): return self.intlk_mon
        if parts.propty.endswith('IntlkLabels-Cte'): return self.intlklabels_cte
        return None

    def set_pv(self, pv_name, value, parts):
        # print(self.psname)
        # for m in self._magnets:
        #     print(m._excitation_curve._filename)

        propty = parts.propty
        deprecated_pvs = {}
        if propty.endswith('Current-SP'):
            value_prev = self.current_rb
            if value != value_prev:
                self.current_sp = value
                deprecated_pvs[pv_name.replace('-SP','-RB')] = self.current_rb
                deprecated_pvs[pv_name.replace('Current-SP','CurrentRef-Mon')] = self.currentref_mon
                deprecated_pvs[pv_name.replace('-SP','-Mon')] = self.current_mon
        elif propty.endswith('PwrState-Sel'):
            value_prev = self.pwrstate_sts
            if value != value_prev:
                self.pwrstate_sel = value
                deprecated_pvs[pv_name.replace('-Sel','-Sts')] = self.pwrstate_sts
                deprecated_pvs[pv_name.replace('PwrState-Sel','CurrentRef-Mon')] = self.currentref_mon
                deprecated_pvs[pv_name.replace('PwrState-Sel','Current-Mon')] = self.current_mon
        elif propty.endswith('OpMode-Sel'):
            value_prev = self.opmode_sts
            if value != value_prev:
                value_sts = self.opmode_sts
                self.opmode_sel = value
                if self.opmode_sel != value:
                    deprecated_pvs[pv_name] = self.opmode_sts
                if self.opmode_sts != value_sts:
                    deprecated_pvs[pv_name.replace('OpMode-Sel','OpMode-Sts')] = self.opmode_sts
        elif propty.endswith('Reset-Cmd'):
            value_prev = self.reset
            self.reset = value
            deprecated_pvs[pv_name] = self.reset
        elif propty.endswith('Abort-Cmd'):
            value_prev = self.abort
            self.abort = value
            deprecated_pvs[pv_name] = self.abort
        elif propty.endswith('WfmLabel-SP'):
            value_prev = self.wfmlabel_rb
            if value != value_prev:
                self.wfmlabel_sp = value
                deprecated_pvs[pv_name.replace('-SP','-RB')] = self.wfmlabel_rb
        elif propty.endswith('WfmData-SP'):
            value_prev = self.wfmdata_sp
            if (value != value_prev).any():
                self.wfmdata_sp = value
                deprecated_pvs[pv_name.replace('-SP','-RB')] = self.wfmdata_rb
        elif propty.endswith('WfmLoad-Sel'):
            value_prev = self.wfmload_sts
            if value != value_prev:
                self.wfmload_sel = value
                deprecated_pvs[pv_name.replace('-Sel','-Sts')] = self.wfmload_sts
        elif propty.endswith('WfmSave-Cmd'):
            self.wfmsave_cmd = value
            deprecated_pvs[pv_name] = self.wfmsave_cmd

        if deprecated_pvs: self.process()
        return deprecated_pvs


class FamilyPowerSupply(PowerSupply):

    def __init__(self, magnets, model, psname, current=None):
        """Initialises current from average integrated field in magnets"""
        super().__init__(magnets, model=model, psname=psname)
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

    def __init__(self, magnets, model, psname, current=None):
        super().__init__(magnets, model=model, psname=psname)
        if len(magnets) > 1:
            raise Exception('Individual Power Supply')
        elif (current is None) and (len(magnets) > 0):
            m = list(magnets)[0]
            total_current = m.get_current_from_field()
            power_supplies = m._power_supplies.difference({self})
            ps_current = 0.0
            for ps in power_supplies:
                ps_current += ps.current_mon
            self.current_sp = (total_current - ps_current) if _math.fabs((total_current - ps_current))> 1e-10 else 0.0
        else:
            self.current_sp = 0.0


class PulsedMagnetPowerSupply(IndividualPowerSupply):

    def __init__(self, magnets, model, psname, current=None):
        super().__init__(magnets, model=model, psname=psname)
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
