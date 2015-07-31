
import os
import numpy
import time
import mathphys
import pyaccel
from . import model
from . import beam_charge
from . import magnet
from . import power_supply
from . import utils


UNDEF_VALUE = 0.0


class AcceleratorModel(model.Model):
    def __init__(self, pipe, interval):
        super().__init__(pipe, interval)
        self._reset('start', self.model_module.lattice_version)
        self._init_magnets_and_power_supplies()
        self._init_sp_pv_values()

    # --- methods implementing response of model to get requests

    def _get_pv(self, pv_name):
        value = self._get_pv_dynamic(pv_name)
        if value is None:
            value = self._get_pv_static(pv_name)
        if value is None:
            value = self._get_pv_fake(pv_name)
        if value is None:
            value = self._get_pv_timing(pv_name)
        if value is None:
            raise Exception('response to ' + pv_name + ' not implemented in model get_pv')
        return value

    def _get_pv_static(self, pv_name):
        # Process global parameters
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
        elif ('PS-' in pv_name or 'PU' in pv_name) and 'TI-' not in pv_name:
            return self._power_supplies[pv_name].current
        else:
            return None

    def _get_pv_fake(self, pv_name):
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

    def _get_pv_dynamic(self, pv_name):
        return None

    def _get_pv_timing(self, pv_name):
        return None

  # --- methods implementing response of model to set requests

    def _set_pv(self, pv_name, value):
        if self._set_pv_magnets(pv_name, value): return
        if self._set_pv_rf(pv_name, value): return
        if self._set_pv_fake(pv_name, value): return
        if self._set_pv_timing(pv_name, value): return

    def _set_pv_magnets(self, pv_name, value):
        if 'PS' in pv_name or 'PU' in pv_name:
            ps = self._power_supplies[pv_name]
            prev_value = ps.current
            if value != prev_value:
                ps.current = value
                self._state_deprecated = True
            return True
        return False

    def _set_pv_fake(self, pv_name, value):
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

    def _set_pv_rf(self, pv_name, value):
        return False

    def _set_pv_timing(self, pv_name, value):
        return False

    # --- methods that help updating the model state

    def _init_sp_pv_values(self):
        utils.log('init', 'epics sp memory for %s pvs'%self.prefix)
        sp_pv_list = []
        for pv in self.pv_module.get_read_write_pvs():
            value = self._get_pv(pv)
            sp_pv_list.append((pv,value))
        self._pipe.send(('sp', sp_pv_list ))

    def _beam_inject(self, charge=None):
        if charge is None: return
        efficiency = 1.0 - self._injection_loss_fraction
        charge = [bunch_charge * efficiency for bunch_charge in charge]
        self._beam_charge.inject(charge)
        return efficiency

    def _beam_eject(self):
        efficiency = 1.0 - self._ejection_loss_fraction
        charge = self._beam_charge.value
        final_charge = [charge_bunch * efficiency for charge_bunch in charge]
        self._beam_charge.dump()
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

    def _set_vacuum_chamber(self, indices='open'):
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
        accelerator_data = self.model_module.accelerator_data
        magnet_names = self.model_module.record_names.get_magnet_names()
        family_mapping = self.model_module.family_mapping
        excitation_curve_mapping = self.model_module.excitation_curves.get_excitation_curve_mapping()
        _, ps2magnet = self.model_module.power_supplies.get_magnet_mapping()

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
                m = magnet.DipoleMagnet(accelerator, indices, filename)
            elif family_type == 'quadrupole':
                m = magnet.QuadrupoleMagnet(accelerator, indices, filename)
            elif family_type == 'sextupole':
                m = magnet.SextupoleMagnet(accelerator, indices, filename)
            elif family_type in ('slow_horizontal_corrector', 'fast_horizontal_corrector', 'horizontal_corrector'):
                m = magnet.HorizontalCorrectorMagnet(accelerator, indices, filename)
            elif family_type in ('slow_vertical_corrector', 'fast_vertical_corrector', 'vertical_corrector'):
                m = magnet.VerticalCorrectorMagnet(accelerator, indices, filename)
            elif family_type == 'skew_quadrupole':
                m = magnet.SkewQuadrupoleMagnet(accelerator, indices, filename)
            elif family_type in 'septum':
                m = magnet.SeptumMagnet(accelerator, indices, filename)
            else:
                m = None

            if m is not None:
                self._magnets[magnet_name] = m

        # Set initial current values
        self._power_supplies = dict()
        for ps_name in ps2magnet.keys():
            magnets = set()
            for magnet_name in ps2magnet[ps_name]:
                if magnet_name in self._magnets:
                    magnets.add(self._magnets[magnet_name])
            if '-FAM' in ps_name:
                ps = power_supply.FamilyPowerSupply(magnets, model = self)
                self._power_supplies[ps_name] = ps

        for ps_name in ps2magnet.keys():
            magnets = set()
            for magnet_name in ps2magnet[ps_name]:
                if magnet_name in self._magnets:
                    magnets.add(self._magnets[magnet_name])
            if not '-FAM' in ps_name:
                ps = power_supply.IndividualPowerSupply(magnets, model = self)
                self._power_supplies[ps_name] = ps

    def _get_parameters_from_upstream_accelerator(self, **kwargs):
        self._injection_parameters = kwargs
        self._upstream_accelerator_state_deprecated = True

    def _send_parameters_to_downstream_accelerator(self, twiss, parameters):
        prefix = self._downstream_accelerator_prefix
        args_dict = parameters
        args_dict['init_twiss'] = twiss.make_dict()
        function = 'get_parameters_from_upstream_accelerator'
        self._pipe.send(('p', (prefix, function, args_dict)))

    def _send_charge_to_downstream_accelerator(self, charge):
        prefix = self._downstream_accelerator_prefix
        args_dict = {}
        args_dict['charge'] = charge

        function = 'get_charge_from_upstream_accelerator'
        self._pipe.send(('p', (prefix, function, args_dict)))
