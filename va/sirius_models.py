
from va.model import TRACK6D, VCHAMBER
from va.model_tline import TLineModel
from va.model_ring import RingModel
from va.model_timing import TimingModel
import va.utils as utils
import sirius
import pyaccel


#--- sirius-specific model classes ---#

class LiModel(TLineModel):

    _prefix = 'LI'
    _model_module = sirius.li
    _single_bunch_mode   = True
    _pulse_duration      = sirius.li.pulse_duration_interval[1]
    _frequency           = sirius.li.frequency
    _nr_bunches          = int(_frequency*_pulse_duration/6)
    _delta_rx, _delta_angle = sirius.coordinate_system.parameters('LI')

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(all_pvs=all_pvs, log_func=log_func)
        self._beam_charge = utils.BeamCharge(nr_bunches=self._nr_bunches)
        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.li_changed = True

    def _get_twiss(self, index):
        self.update_state()
        if isinstance(index, str):
            if index == 'end':
                sirius.li.accelerator_data['twiss_at_exit']
        else:
            Exception('index in _get_twiss invalid for LI')

    def _get_equilibrium_at_maximum_energy(self):
        li = self._driver.li_model
        li.update_state()
        eq = dict()
        eq['emittance'] =  sirius.li.accelerator_data['emittance']
        eq['energy_spread'] = sirius.li.accelerator_data['energy_spread']
        eq['global_coupling'] = sirius.li.accelerator_data['global_coupling']
        eq['twiss_at_exit'] = sirius.li.accelerator_data['twiss_at_exit']
        return eq


class TbModel(TLineModel):

    _prefix = 'TB'
    _model_module = sirius.tb
    _delta_rx, _delta_angle = sirius.coordinate_system.parameters('TB')
    _nr_bunches = sirius.bo.harmonic_number

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(all_pvs=all_pvs, log_func=log_func)
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=self._nr_bunches)
        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.tb_changed = True

    def _get_equilibrium_at_maximum_energy(self):
        li = self._driver.li_model
        li.update_state()
        eq = li._get_equilibrium_at_maximum_energy()
        return eq

    def _get_parameters_from_upstream_accelerator(self):
        li = self._driver.li_model
        li.update_state()
        eq = li._get_equilibrium_at_maximum_energy()
        eq['twiss_at_entrance'] = eq.pop('twiss_at_exit')
        return eq


class BoModel(RingModel):

    _prefix = 'BO'
    _model_module = sirius.bo
    _delta_rx, _delta_angle = sirius.coordinate_system.parameters('BO')
    _nr_bunches = _model_module.harmonic_number

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(all_pvs=all_pvs, log_func=log_func)
        #self._accelerator.energy = 0.15e9 # [eV]
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=self._nr_bunches)
        self._calc_lifetimes()
        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.bo_changed = True

    def reset(self, message1='reset', message2='', c='white', a=None):
        super().reset(message1=message1, message2=message2, c=c, a=a)
        injection_point = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'sept_in')[0]
        self._accelerator = pyaccel.lattice.shift(self._accelerator, start = injection_point)
        self._record_names = utils.shift_record_names(self._accelerator, self._record_names)
        self._ext_point = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'sept_ex')[0]
        self._kickin_idx = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'kick_in')
        self._kickex_idx = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'kick_ex')
        self._kickin_angle = -0.01934 # FIX ME! : hardcoded value
        self._kickex_angle =  0.00132 # FIX ME! : hardcoded value

    def _get_equilibrium_at_maximum_energy(self):
        # this has to be calculated everytime BO changes
        eq = dict()
        eq['emittance'] = self._summary['natural_emittance']
        eq['energy_spread'] = self._summary['natural_energy_spread']
        eq['global_coupling'] = sirius.bo.accelerator_data['global_coupling']
        return eq

    def _get_parameters_from_upstream_accelerator(self):
        tb = self._driver.tb_model
        tb.update_state()
        eq = tb._get_equilibrium_at_maximum_energy()
        eq['twiss_at_entrance'] =  tb._get_twiss('end')
        return eq

class TsModel(TLineModel):

    _prefix = 'TS'
    _model_module = sirius.ts
    _delta_rx, _delta_angle = sirius.coordinate_system.parameters('TS')
    _nr_bunches = sirius.bo.harmonic_number

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(all_pvs=all_pvs, log_func=log_func)
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=self._nr_bunches)
        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.ts_changed = True

    def _get_equilibrium_at_maximum_energy(self):
        bo = self._driver.bo_model
        bo.update_state()
        eq = bo._get_equilibrium_at_maximum_energy()
        return eq

    def _get_parameters_from_upstream_accelerator(self):
        bo = self._driver.bo_model
        bo.update_state()
        eq = bo._get_equilibrium_at_maximum_energy()
        eq['twiss_at_entrance'] =  bo._ejection_twiss[-1]
        return eq


class SiModel(RingModel):

    _prefix = 'SI'
    _model_module = sirius.si
    _delta_rx, _delta_angle = sirius.coordinate_system.parameters('SI')
    _nr_bunches = _model_module.harmonic_number

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(all_pvs=all_pvs, log_func=log_func)
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=self._nr_bunches)
        self._calc_lifetimes()
        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.si_changed = True

    def _get_parameters_from_upstream_accelerator(self):
        ts = self._driver.ts_model
        ts.update_state()
        eq = ts._get_equilibrium_at_maximum_energy()
        eq['twiss_at_entrance'] = ts._get_twiss('end')
        return eq

class TiModel(TimingModel):

    _prefix = 'TI'
    _model_module = sirius.ti

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(all_pvs=all_pvs, log_func=log_func)
        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.ti_changed = True
