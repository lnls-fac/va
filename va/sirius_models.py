
from va.model import TRACK6D, VCHAMBER
from va.model_tline import TLineModel
from va.model_ring import RingModel
from va.model_timing import TimingModel
import va.utils as utils
import sirius
import pyaccel
import numpy


#--- sirius-specific model classes ---#

class LiModel(TLineModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.li, all_pvs=all_pvs, log_func=log_func)
        self._single_bunch_mode   = True
        self._pulse_duration      = sirius.li.pulse_duration_interval[1]
        self._state_deprecated = True
        self.notify_driver()

        # vacuum chamber
        self._hmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmin'))
        self._hmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmax'))
        self._vmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmin'))
        self._vmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmax'))
        self._hmin = numpy.append(self._hmin, self._hmin[-1])
        self._hmax = numpy.append(self._hmax, self._hmax[-1])
        self._vmin = numpy.append(self._vmin, self._vmin[-1])
        self._vmax = numpy.append(self._vmax, self._vmax[-1])

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
        eq['emittance'] =  sirius.li.accelerator_data['emittance']
        eq['energy_spread'] = sirius.li.accelerator_data['energy_spread']
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

        # vacuum chamber
        self._hmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmin'))
        self._hmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmax'))
        self._vmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmin'))
        self._vmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmax'))
        self._hmin = numpy.append(self._hmin, self._hmin[-1])
        self._hmax = numpy.append(self._hmax, self._hmax[-1])
        self._vmin = numpy.append(self._vmin, self._vmin[-1])
        self._vmax = numpy.append(self._vmax, self._vmax[-1])

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

        # vacuum chamber
        self._hmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmin'))
        self._hmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmax'))
        self._vmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmin'))
        self._vmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmax'))

        self._beam_charge = utils.BeamCharge(nr_bunches=self._accelerator.harmonic_number)
        self._calc_lifetimes()

    def notify_driver(self):
        if self._driver: self._driver.bo_changed = True

    def reset(self, message1='reset', message2='', c='white', a=None):
        super().reset(message1=message1, message2=message2, c=c, a=a)
        injection_point = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'sept_in')[0]
        self._accelerator = pyaccel.lattice.shift(self._accelerator, start = injection_point)
        self._record_names = shift_record_names(self._accelerator, self._record_names)

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
        init_twiss = tb._get_twiss('end')
        init_pos = init_twiss.fixed_point
        init_pos = self._transform_to_local_coordinates(init_pos, -0.03, 0.0143) #FIX ME! : hardcoded value
        init_twiss.fixed_point = init_pos
        eq['twiss_at_entrance'] =  init_twiss
        return eq

class TsModel(TLineModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.ts, all_pvs=all_pvs, log_func=log_func)
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=sirius.bo.harmonic_number)
        self._state_deprecated = True
        self.notify_driver()

        # vacuum chamber
        self._hmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmin'))
        self._hmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmax'))
        self._vmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmin'))
        self._vmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmax'))
        self._hmin = numpy.append(self._hmin, self._hmin[-1])
        self._hmax = numpy.append(self._hmax, self._hmax[-1])
        self._vmin = numpy.append(self._vmin, self._vmin[-1])
        self._vmax = numpy.append(self._vmax, self._vmax[-1])

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
        init_twiss = bo._ejection_twiss[-1]
        init_twiss.fixed_point = self._transform_to_local_coordinates(init_twiss.fixed_point, -0.022, -0.005) #FIX ME! : hardcoded value
        eq['twiss_at_entrance'] =  init_twiss
        return eq


class SiModel(RingModel):

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(sirius.si, all_pvs=all_pvs, log_func=log_func)
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=self._accelerator.harmonic_number)
        self._calc_lifetimes()

        # vacuum chamber
        self._hmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmin'))
        self._hmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmax'))
        self._vmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmin'))
        self._vmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmax'))

    def notify_driver(self):
        if self._driver: self._driver.si_changed = True

    def _get_parameters_from_upstream_accelerator(self):
        ts = self._driver.ts_model
        ts.update_state()
        eq = ts._get_equilibrium_at_maximum_energy()
        init_twiss = ts._get_twiss('end')
        init_twiss.fixed_point = self._transform_to_local_coordinates(init_twiss.fixed_point, -0.0165 , 0.00219 ) #FIX ME! : hardcoded value
        eq['twiss_at_entrance'] = init_twiss
        return eq

class TiModel(TimingModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.ti, all_pvs=all_pvs, log_func=log_func)
        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.ti_changed = True


# --- auxilliary methods

def shift_record_names(accelerator, record_names_dict):
    new_dict = {}
    for key in record_names_dict.keys():
        new_dict[key] = {}
        for k in record_names_dict[key].keys():
            new_dict[key][k]= record_names_dict[key][k]
    length = len(accelerator)
    start = pyaccel.lattice.find_indices(accelerator, 'fam_name', 'start')[0]
    for value in new_dict.values():
        for key in value.keys():
            indices = value[key]
            new_indices = shift_indices(indices, length, start)
            value[key] = new_indices
    return new_dict

def shift_indices(indices, length, start):
    try:
        new_indices = indices[:]
        for i in range(len(new_indices)):
            if isinstance(new_indices[i], int):
                new_indices[i] = (new_indices[i] + start)%(length)
            else:
                new_indices[i] = shift_indices(new_indices[i], length, start)
        return new_indices
    except:
        new_indices = (indices+start)%(length)
        return new_indices
