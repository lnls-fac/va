
import math as _math
import numpy as _np
from siriuspy.pwrsupply.simul.model import PowerSupply as _PowerSupply


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

        self._propty_db = self.propty_database
        self.propties = {
            'Current-SP': 'current_sp',
            'Current-RB': 'current_rb',
            'CurrentRef-Mon': 'currentref_mon',
            'Current-Mon': 'current_mon',
            'PwrState-Sel': 'pwrstate_sel',
            'PwrState-Sts': 'pwrstate_sts',
            'OpMode-Sel': 'opmode_sel',
            'OpMode-Sts': 'opmode_sts',
            'CtrlMode-Mon': 'ctrlmode_mon',
            'Reset-Cmd': 'reset',
            'Abort-Cmd': 'abort',
            'WfmIndex-Mon': 'wfmindex_mon',
            'WfmLabels-Mon': 'wfmlabels_mon',
            'WfmLabel-SP': 'wfmlabel_sp',
            'WfmLabel-RB': 'wfmlabel_rb',
            'WfmData-SP': 'wfmdata_sp',
            'WfmData-RB': 'wfmdata_rb',
            'WfmSave-Cmd': 'wfmsave_cmd',
            'WfmLoad-Sel': 'wfmload_sel',
            'WfmLoad-Sts': 'wfmload_sts',
            'Intlk-Mon': 'intlk_mon',
            'IntlkLabels-Cte': 'intlklabels_cte',
        }

    def process(self):
        for m in self._magnets:
            m.process()

    def get_pv(self, pv_name, parts):
        if parts.propty in self.propties.keys():
            return getattr(self, self.propties[parts.propty])
        if parts.propty in self._propty_db:
            return self._propty_db[parts.propty]['value']
        return None

    def set_pv(self, pv_name, value, parts):
        propty = parts.propty
        if not propty.endswith(('-SP','-Sel','-Cmd')) or not propty in self.propties.keys(): return

        old_values = {}
        for k,v in self.propties.items():
            if k.startswith(('WfmData','WfmLabels-Mon')): continue
            old_values[k] = getattr(self,v)

        setattr(self,self.propties[propty],value)
        self.process()

        deprecated = {}
        if propty == 'WfmData-SP':
            deprecated[propty] = value
        for k,v in old_values.items():
            new_v = getattr(self, self.propties[k])
            if v != new_v:   deprecated[k] = new_v
        if 'WfmData-SP' in deprecated or 'WfmLoad-Sel' in deprecated:
            deprecated['WfmData-RB'] = getattr(self,self.propties['WfmData-RB'])
        if 'WfmLabel-SP' in deprecated:
            deprecated['WfmLabels-Mon'] = getattr(self, self.propties['WfmLabels-Mon'])

        deprec = {}
        for k,v in deprecated.items():
            if k.endswith(('-SP','-Sel')): continue
            deprec[pv_name.replace(propty,k)] = v

        return deprec


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
