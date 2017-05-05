
import math
from . import magnet
import siriuspy
from siriuspy.pwrsupply.controller import _controller_wfmlabels
from siriuspy.pwrsupply.controller import ControllerSim as _ControllerSim

# These classes should be deprecated!
# Corresponding classes should be implemented in siriuspy and used! (X.R.R.)


class PowerSupply(object):

    def __init__(self, magnets, model, ps_name):
        """Gets and sets current [A]
        Connected magnets are processed after current is set.
        """
        self._model = model
        self._ps_name = ps_name
        self._magnets = magnets
        #self._controller = _ControllerSim(current_std=0.0)
        self._pwr_state = 1  # [On]
        self.ctrl_mode = 0
        self._current_sp = 0
        self._current_rb = self._current_sp
        self._currentref = self._current_rb
        self._current_load = self._currentref
        self._wfmindex = 0
        self._wfmlabels = [label for label in _controller_wfmlabels]
        self._wfmslot = 0
        self._waveform = siriuspy.pwrsupply.PSWaveForm.wfm_constant(self._wfmlabels[0])
        self._op_mode = 0
        self._interlock = 0
        for m in magnets:
            m.add_power_supply(self)

    @property
    def interlock(self):
        return self._interlock

    @property
    def current_sp(self):
        return self._current_sp

    @property
    def current_rb(self):
        return self._current_rb

    @property
    def current_load(self):
        return self._current_load

    @property
    def currentref(self):
        return self._currentref

    @property
    def pwr_state(self):
        return self._pwr_state

    @property
    def wfmindex(self):
        return self._wfmindex

    @property
    def wfmlabels(self):
        return [label for label in self._wfmlabels]

    @property
    def wfmlabel(self):
        return self._waveform.label

    @wfmlabel.setter
    def wfmlabel(self, value):
        self._waveform.label = value

    @property
    def op_mode(self):
        return self._op_mode

    def _current_load_setter(self, value): # called only from within this class
        self._current_rb = value
        self._currentref = self._current_rb
        self._current_load = self._currentref
        for m in self._magnets:
            m.process()

    @current_sp.setter
    def current_sp(self, value):
        if self.ctrl_mode == 1: return # CtrlState: Local
        self._current_sp = value
        if self._pwr_state and self.op_mode == 0:
            self._current_load_setter(value)

    @pwr_state.setter
    def pwr_state(self, value):
        if self.ctrl_mode == 1: return # ctrl_mode: Local
        self._pwr_state = value
        if value == 0:
            self._current_load_setter(0)
        else:
            self._current_load_setter(self._current_sp)

    @op_mode.setter
    def op_mode(self, value):
        if self.ctrl_mode == 1: return # ctrl_mode: Local
        self._op_mode = value


class FamilyPowerSupply(PowerSupply):

    def __init__(self, magnets, model, ps_name, current=None):
        """Initialises current from average integrated field in magnets"""
        super().__init__(magnets, model=model, ps_name=ps_name)
        if (current is None) and (len(magnets) > 0):
            total_current = 0.0
            n = 0
            for m in magnets:
                total_current += m.get_current_from_field()
                n += 1
            self.current_sp = total_current/n
        else:
            self.current_sp = 0.0

    @property
    def current_sp(self):
        return self._current_sp

    @current_sp.setter
    def current_sp(self, value):
        if self.ctrl_mode == 1: return # CtrlState: Local
        if isinstance(list(self._magnets)[0], magnet.BoosterDipoleMagnet):
            all_power_supplies = self._model._power_supplies.values()
            booster_bend_ps = []
            for ps in all_power_supplies:
                if isinstance(list(ps._magnets)[0], magnet.BoosterDipoleMagnet):
                    booster_bend_ps.append(ps)
                    self._current_sp = value
                    if self._pwr_state and self.op_mode == 0:
                        self._current_load_setter(value)

            # Change the accelerator energy
            change_energy = True
            for ps in booster_bend_ps:
                for m in ps._magnets:
                    m.process(change_energy=change_energy)
                    change_energy = False

            # Change strengths of all magnets when accelerator energy is changed
            for ps in all_power_supplies:
                for m in ps._magnets: m.renormalize_magnet()

        else:
            self._current_sp = value
            if self._pwr_state and self.op_mode == 0:
                self._current_load_setter(value)


class IndividualPowerSupply(PowerSupply):

    def __init__(self, magnets, model, ps_name, current=None):
        super().__init__(magnets, model=model, ps_name=ps_name)
        if len(magnets) > 1:
            raise Exception('Individual Power Supply')
        elif (current is None) and (len(magnets) > 0):
            m = list(magnets)[0]
            total_current = m.get_current_from_field()
            power_supplies = m._power_supplies.difference({self})
            ps_current = 0.0
            for ps in power_supplies:
                ps_current += ps.current_load
            self.current_sp = (total_current - ps_current) if math.fabs((total_current - ps_current))> 1e-10 else 0.0
        else:
            self.current_sp = 0.0


class PulsedMagnetPowerSupply(IndividualPowerSupply):

    def __init__(self, magnets, model, ps_name, current=None):
        super().__init__(magnets, model=model, ps_name=ps_name)
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
