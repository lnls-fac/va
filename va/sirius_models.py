
from va.model import TRACK6D, VCHAMBER
from va.model_tline import TLineModel
from va.model_ring import RingModel
from va.model_timing import TimingModel
import va.utils as utils
import sirius
import pyaccel


#--- sirius-specific model classes ---#

class LiModel(TLineModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.li, all_pvs=all_pvs, log_func=log_func)
        self._single_bunch_mode   = True
        self._pulse_duration      = sirius.li.pulse_duration_interval[1]

        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.li_changed = True

    def _get_twiss(self, index):
        self.update_state()
        if isinstance(index, str):
            if index == 'end':
                return sirius.tb.initial_twiss
            elif index == 'begin':
                Exception('index in _get_twiss invalid for LI')
        else:
            Exception('index in _get_twiss invalid for LI')

    def _get_equilibrium_at_maximum_energy(self):
        li = self._driver.li_model
        li.update_state()
        eq = dict()
        eq['emittance'] =  sirius.li.accelerator_data['emittance']        # FIX ME! : hardcoded value
        eq['energy_spread'] = sirius.li.accelerator_data['energy_spread'] # FIX ME! : hardcoded value
        eq['global_coupling'] = sirius.li.accelerator_data['global_coupling']
        return eq


class TbModel(TLineModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.tb, all_pvs=all_pvs, log_func=log_func)
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=sirius.bo.harmonic_number)
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
        eq['twiss_at_entrance'] = li._get_twiss('end')
        return eq


class BoModel(RingModel):

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(sirius.bo, all_pvs=all_pvs, log_func=log_func)
        #self._accelerator.energy = 0.15e9 # [eV]
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER

        self._beam_charge = utils.BeamCharge(nr_bunches=self._accelerator.harmonic_number)
        #self._beam_charge.inject(0.0) # [coulomb]
        self._init_families_str()
        self._calc_lifetimes()

    def notify_driver(self):
        if self._driver: self._driver.bo_changed = True

    def _get_equilibrium_at_maximum_energy(self):
        # this has to be calculated everytime BO changes
        eq = dict()
        eq['emittance'] = self._summary['natural_emittance'] #3.4749e-09     # FIX ME! : hardcoded value
        eq['energy_spread'] = self._summary['natural_energy_spread'] #8.7427e-04  # FIX ME! : hardcoded value
        eq['global_coupling'] = sirius.bo.accelerator_data['global_coupling']
        return eq

    def _get_parameters_from_upstream_accelerator(self):
        tb = self._driver.tb_model
        tb.update_state()
        eq = tb._get_equilibrium_at_maximum_energy()
        eq['twiss_at_entrance'] = tb._get_twiss('end')
        return eq

class TsModel(TLineModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.ts, all_pvs=all_pvs, log_func=log_func)
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=sirius.bo.harmonic_number)
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
        idx = pyaccel.lattice.find_indices(bo._accelerator, 'fam_name', 'sept_ex')
        eq['twiss_at_entrance'] = bo._get_twiss(idx[0])
        return eq


class SiModel(RingModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.si, all_pvs=all_pvs, log_func=log_func)
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=self._accelerator.harmonic_number)
        self._init_families_str()
        self._calc_lifetimes()

    def notify_driver(self):
        if self._driver: self._driver.si_changed = True

    def _get_parameters_from_upstream_accelerator(self):
        ts = self._driver.ts_model
        ts.update_state()
        eq = ts._get_equilibrium_at_maximum_energy()
        eq['twiss_at_entrance'] = ts._get_twiss('end')
        return eq

class TiModel(TimingModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.ti, all_pvs=all_pvs, log_func=log_func)
        # if self._delay_bo2si_delta is None:
        #     rfrequency = self._driver.si_model.get_pv('SIRF-FREQUENCY')
        #     self._delay_bo2si_delta = 1.0 / rfrequency
        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.ti_changed = True
