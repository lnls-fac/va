import os
import numpy
import mathphys
import pyaccel
from va.model import Model, UNDEF_VALUE
from va import utils


class AcceleratorModel(Model):

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(all_pvs=all_pvs, log_func=log_func)
        self.reset('start',self._model_module.lattice_version)
        self._init_magnets_and_power_supplies()
        self._set_vacuum_chamber(indices='open')

    # --- methods implementing response of model to get requests

    def get_pv(self, pv_name):
        value = self.get_pv_dynamic(pv_name)
        if value is None:
            value = self.get_pv_static(pv_name)
        if value is None:
            value = self.get_pv_fake(pv_name)
        if value is None:
            raise Exception('response to ' + pv_name + ' not implemented in model get_pv')
        return value

    def get_pv_dynamic(self, pv_name):
        return None

    def get_pv_static(self, pv_name):
        # process global parameters
        if '-BPM-' in pv_name:
            charge = self._beam_charge.total_value
            idx = self._get_elements_indices(pv_name)
            if 'FAM-X' in pv_name:
                if self._orbit is None or charge == 0.0: return [UNDEF_VALUE]*len(idx)
                return self._orbit[0,idx]
            elif 'FAM-Y' in pv_name:
                if self._orbit is None or charge == 0.0: return [UNDEF_VALUE]*len(idx)
                return self._orbit[2,idx]
            else:
                if self._orbit is None or charge == 0.0: return [UNDEF_VALUE]*2
                return self._orbit[[0,2],idx[0]]
        elif 'PS-' in pv_name or 'PU' in pv_name:
            return self._power_supplies[pv_name].current
        else:
            return None

    def get_pv_fake(self, pv_name):
        if '-ERRORX' in pv_name:
            idx = self._get_elements_indices(pv_name)
            error = pyaccel.lattice.get_error_misalignment_x(self._accelerator, idx[0])
            return error
        if '-ERRORY' in pv_name:
            idx = self._get_elements_indices(pv_name)
            error = pyaccel.lattice.get_error_misalignment_y(self._accelerator, idx[0])
            return error
        if '-ERRORR' in pv_name:
            idx = self._get_elements_indices(pv_name)
            error = pyaccel.lattice.get_error_rotation_roll(self._accelerator, idx[0])
            return error
        else:
            return None

  # --- methods implementing response of model to set requests

    def set_pv(self, pv_name, value):
        if self.set_pv_magnets(pv_name, value): return
        if self.set_pv_rf(pv_name, value): return
        if self.set_pv_fake(pv_name, value): return

    def set_pv_magnets(self, pv_name, value):
        if 'PS' in pv_name or 'PU' in pv_name:
            ps = self._power_supplies[pv_name]
            prev_value = ps.current
            if value != prev_value:
                ps.current = value
                self._state_deprecated = True
            return True
        return False

    def set_pv_rf(self, pv_name, value):
        return False

    def set_pv_fake(self, pv_name, value):
        if '-ERRORX' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorx = pyaccel.lattice.get_error_misalignment_x(self._accelerator, idx[0])
            if value != prev_errorx:
                pyaccel.lattice.set_error_misalignment_x(self._accelerator, idx, value)
                self._state_deprecated = True
            return True
        elif '-ERRORY' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errory = pyaccel.lattice.get_error_misalignment_y(self._accelerator, idx[0])
            if value != prev_errory:
                pyaccel.lattice.set_error_misalignment_y(self._accelerator, idx, value)
                self._state_deprecated = True
            return True
        elif '-ERRORR' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorr = pyaccel.lattice.get_error_rotation_roll(self._accelerator, idx[0])
            if value != prev_errorr:
                pyaccel.lattice.set_error_rotation_roll(self._accelerator, idx, value)
                self._state_deprecated = True
            return True
        return False

    # --- methods that help updating the model state

    def reset(self, message1='reset', message2='', c='white', a=None):
        if self._all_pvs is None:
            self._record_names = self._model_module.record_names.get_record_names()
        else:
            self._record_names = self._all_pvs
        self._accelerator = self._model_module.create_accelerator()
        self._beam_charge = utils.BeamCharge(nr_bunches = self._nr_bunches)
        self.beam_dump(message1,message2,c,a)
        self._set_vacuum_chamber(indices='open')

    def beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        self._state_deprecated = True
        if self._beam_charge: self._beam_charge.dump()
        self._orbit = None
        self._twiss = None
        self._m66 = None
        self._transfer_matrices = None
        self._summary = None
        self._injection_loss_fraction = None
        self._ejection_loss_fraction = None
    
    def beam_inject(self, delta_charge, message1='inject', message2 = '', c='white', a=None):
        if message1 and message1 != 'cycle':
            self._log(message1, message2, c=c, a=a)
        efficiency = 1.0 - self._injection_loss_fraction
        delta_charge = [delta_charge_bunch * efficiency for delta_charge_bunch in delta_charge]
        self._beam_charge.inject(delta_charge)
        final_charge = self._beam_charge.value
        #if message1 == 'cycle':
        #    self._log(message1 = 'cycle', message2 = '  beam injection in {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency), c='white')
        return final_charge, efficiency

    def beam_eject(self, message1='eject', message2 = '', c='white', a=None):
        if message1 and message1 != 'cycle':
            self._log(message1, message2, c=c, a=a)
        efficiency = 1.0 - self._ejection_loss_fraction
        charge = self._beam_charge.value
        final_charge = [charge_bunch * efficiency for charge_bunch in charge]
        self._beam_charge.dump()
        #if message1 == 'cycle':
        #    self._log(message1 = 'cycle', message2 = 'beam ejection from {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency), c='white')
        return final_charge, efficiency


   # --- auxilliary methods

    def _get_elements_indices(self, pv_name):
        """Get flattened indices of element in the model"""
        data = self._all_pvs[pv_name]
        indices = []
        for key in data.keys():
            idx = mathphys.utils.flatten(data[key])
            indices.extend(idx)
        return indices

    def _set_vacuum_chamber(self, indices = 'open'):
        hmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmin'))
        hmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmax'))
        vmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmin'))
        vmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmax'))
        if indices == 'open':
            self._hmin = hmin
            self._hmax = hmax
            self._vmin = vmin
            self._vmax = vmax
        elif indices == 'closed':
            self._hmin = numpy.append(hmin, hmin[-1])
            self._hmax = numpy.append(hmax, hmax[-1])
            self._vmin = numpy.append(vmin, vmin[-1])
            self._vmax = numpy.append(vmax, vmax[-1])
        else:
            raise Exception("invalid value for indices")

    def _get_parameters_from_upstream_accelerator(self):
        """Return initial Twiss parameters to be tracked"""
        return None

    def _get_equilibrium_at_maximum_energy(self):
        return None

    def _get_twiss(self, index):
        self.update_state()
        if isinstance(index, str):
            if index == 'end':
                return self._twiss[-1]
            elif index == 'begin':
                return self._twiss[0]
        else:
            return self._twiss[index]

    def _get_vacuum_chamber(self, init_idx=None, final_idx=None):
        _dict = {}
        _dict['hmin'] = self._hmin[init_idx:final_idx]
        _dict['hmax'] = self._hmax[init_idx:final_idx]
        _dict['vmin'] = self._vmin[init_idx:final_idx]
        _dict['vmax'] = self._vmax[init_idx:final_idx]
        return _dict

    def _get_coordinate_system_parameters(self):
        _dict = {}
        _dict['delta_rx'] = self._delta_rx
        _dict['delta_angle'] = self._delta_angle
        return _dict

    def _init_magnets_and_power_supplies(self):
        accelerator = self._accelerator
        accelerator_data = self._model_module.accelerator_data
        magnet_names = self._model_module.record_names.get_magnet_names()
        family_mapping = self._model_module.family_mapping
        excitation_curve_mapping = self._model_module.excitation_curves.get_excitation_curve_mapping()
        _, ps2magnet = self._model_module.power_supplies.get_magnet_mapping()

        self._magnets = dict()
        for magnet_name in magnet_names.keys():
            excitation_curve = excitation_curve_mapping[magnet_name]
            try:
                filename = os.path.join(accelerator_data['dirs']['excitation_curves'], excitation_curve)
            except:
                filename = os.path.join(accelerator_data['dirs']['excitation_curves'], 'not_found')

            family, indices = magnet_names[magnet_name].popitem()
            indices = indices[0]
            family_type = family_mapping[family]
            if family_type == 'dipole':
                magnet = utils.DipoleMagnet(accelerator, indices, filename)
            elif family_type == 'quadrupole':
                magnet = utils.QuadrupoleMagnet(accelerator, indices, filename)
            elif family_type == 'sextupole':
                magnet = utils.SextupoleMagnet(accelerator, indices, filename)
            elif family_type in ('slow_horizontal_corrector', 'fast_horizontal_corrector', 'horizontal_corrector'):
                magnet = utils.HorizontalCorrectorMagnet(accelerator, indices, filename)
            elif family_type in ('slow_vertical_corrector', 'fast_vertical_corrector', 'vertical_corrector'):
                magnet = utils.VerticalCorrectorMagnet(accelerator, indices, filename)
            elif family_type == 'skew_quadrupole':
                magnet = utils.SkewQuadrupoleMagnet(accelerator, indices, filename)
            elif family_type in 'septum':
                magnet = utils.SeptumMagnet(accelerator, indices, filename)
            else:
                magnet = None

            if magnet is not None:
                self._magnets[magnet_name] = magnet

        # Set initial current values
        self._power_supplies = dict()
        for ps_name in ps2magnet.keys():
            magnets = set()
            for magnet_name in ps2magnet[ps_name]:
                if magnet_name in self._magnets:
                    magnets.add(self._magnets[magnet_name])
            if '-FAM' in ps_name:
                power_supply = utils.FamilyPowerSupply(magnets)
            else:
                power_supply = utils.IndividualPowerSupply(magnets)
            self._power_supplies[ps_name] = power_supply
