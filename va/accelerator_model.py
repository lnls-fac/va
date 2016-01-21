
import os
import enum
import math
import numpy
import mathphys
import pyaccel
from . import model
from . import magnet
from . import power_supply
from . import utils

_u = mathphys.units
_c = mathphys.constants.light_speed
UNDEF_VALUE = utils.UNDEF_VALUE
TRACK6D = True

class Plane(enum.IntEnum):
    horizontal = 0
    vertical = 1
    longitudinal = 2


class AcceleratorModel(model.Model):

    def __init__(self, **kwargs):
        self._injection_parameters = None
        super().__init__(**kwargs)
        self._reset('start', self.model_module.lattice_version)
        self._init_magnets_and_power_supplies()
        self._init_sp_pv_values()

    # --- methods implementing response of model to get requests

    def _get_pv(self, pv_name):
        value = self._get_pv_dynamic(pv_name)
        if value is None:
            value = self._get_pv_fake(pv_name)
        if value is None:
            value = self._get_pv_static(pv_name)
        if value is None:
            value = self._get_pv_timing(pv_name)
        if value is None:
            raise Exception('response to ' + pv_name + ' not implemented in model get_pv')
        return value

    def _get_pv_static(self, pv_name):
        # Process global parameters
        if ('PS-' in pv_name or 'PU' in pv_name) and 'TI-' not in pv_name:
            return self._power_supplies[pv_name].current
        elif 'EFF' in pv_name:
            if 'TOTAL' in pv_name:
                return 100*self._total_efficiency if self._total_efficiency is not None else UNDEF_VALUE
            elif 'INJ' in pv_name:
                return UNDEF_VALUE
                return 100*self._injection_efficiency if self._injection_efficiency is not None else UNDEF_VALUE
            elif 'EXT' in pv_name:
                return UNDEF_VALUE
                return 100*self._ejection_efficiency if self._ejection_efficiency is not None else UNDEF_VALUE
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
        if '-SAVEFLATFILE' in pv_name:
            return 0
        if '-POS' in pv_name:
            indices = self._get_elements_indices(pv_name, flat=False)
            if isinstance(indices[0], int):
                pos = pyaccel.lattice.find_spos(self._accelerator, indices)
            else:
                pos = [pyaccel.lattice.find_spos(self._accelerator, idx[0]) for idx in indices]
            start = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'start')[0]
            start_spos = pyaccel.lattice.find_spos(self._accelerator, start)
            pos = (pos-start_spos)%(pyaccel.lattice.length(self._accelerator))
            return pos
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
        if ('PS-' in pv_name or 'PU' in pv_name) and 'TI-' not in pv_name:
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
        elif '-SAVEFLATFILE' in pv_name:
            fname = 'flatfile_' + self.model_module.lattice_version + '.txt'
            pyaccel.lattice.write_flat_file(self._accelerator, fname)
            self._send_queue.put(('s', (pv_name, 0)))
            return True
        return False

    def _set_pv_rf(self, pv_name, value):
        return False

    def _set_pv_timing(self, pv_name, value):
        return False

   # --- auxiliary methods

    def _init_sp_pv_values(self):
        utils.log('init', 'epics sp memory for %s pvs'%self.prefix)
        sp_pv_list = []
        for pv in self.pv_module.get_read_write_pvs() + self.pv_module.get_constant_pvs():
            value = self._get_pv(pv)
            sp_pv_list.append((pv,value))
        self._send_queue.put(('sp', sp_pv_list ))

    def _get_elements_indices(self, pv_name, flat=True):
        """Get flattened indices of element in the model"""
        name = pv_name.split(':')[0]
        data = self._all_pvs[name]
        indices = []
        for key in data.keys():
            idx = mathphys.utils.flatten(data[key]) if flat else data[key]
            indices.extend(idx)
        return indices

    def _set_vacuum_chamber(self):
        self._hmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmin'))
        self._hmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'hmax'))
        self._vmin = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmin'))
        self._vmax = numpy.array(pyaccel.lattice.get_attribute(self._accelerator._accelerator.lattice, 'vmax'))

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

    def _append_marker(self):
        marker = pyaccel.elements.marker('marker')
        marker.hmin, marker.hmax = self._accelerator[-1].hmin, self._accelerator[-1].hmax
        marker.vmin, marker.vmax = self._accelerator[-1].vmin, self._accelerator[-1].vmax
        self._accelerator.append(marker)

    def _init_magnets_and_power_supplies(self):
        accelerator = self._accelerator
        accelerator_data = self.model_module.accelerator_data
        magnet_names = self.model_module.device_names.get_magnet_names(self._accelerator)
        family_mapping = self.model_module.family_mapping
        excitation_curve_mapping = self.model_module.excitation_curves.get_excitation_curve_mapping(self._accelerator)
        _, ps2magnet = self.model_module.power_supplies.get_magnet_mapping(self._accelerator)

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
            if family_type in ('dipole', 'septum'):
                if self.prefix == 'BO':
                    m = magnet.BoosterDipoleMagnet(accelerator, indices, filename)
                else:
                    m = magnet.NormalMagnet(accelerator, indices, filename)
            elif family_type == 'quadrupole':
                m = magnet.NormalMagnet(accelerator, indices, filename)
            elif family_type == 'sextupole':
                m = magnet.NormalMagnet(accelerator, indices, filename)
            elif family_type in ('slow_horizontal_corrector', 'fast_horizontal_corrector', 'horizontal_corrector'):
                m = magnet.NormalMagnet(accelerator, indices, filename)
            elif family_type in ('slow_vertical_corrector', 'fast_vertical_corrector', 'vertical_corrector'):
                m = magnet.SkewMagnet(accelerator, indices, filename)
            elif family_type == 'skew_quadrupole':
                m = magnet.SkewMagnet(accelerator, indices, filename)
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
                ps = power_supply.FamilyPowerSupply(magnets, model=self, ps_name=ps_name)
                self._power_supplies[ps_name] = ps

        # It is necessary to initalise all family power supplies before
        for ps_name in ps2magnet.keys():
            magnets = set()
            for magnet_name in ps2magnet[ps_name]:
                if magnet_name in self._magnets:
                    magnets.add(self._magnets[magnet_name])
            if not '-FAM' in ps_name:
                ps = power_supply.IndividualPowerSupply(magnets, model=self, ps_name=ps_name)
                self._power_supplies[ps_name] = ps

    def _send_initialisation_sign(self):
        self._send_queue.put(('i', self.prefix))

    def _send_parameters_to_downstream_accelerator(self, _dict):
        prefix = self._downstream_accelerator_prefix
        self._send_queue.put(('p', (prefix, _dict)))

    def _get_parameters_from_upstream_accelerator(self, _dict):
        if 'path_length' in _dict.keys():
            self._calc_nominal_delays(**_dict)
        elif 'charge' in _dict.keys():
            self._received_charge = True
            self._update_state()
            self._injection_cycle(**_dict)
            self._received_charge = False
        else:
            self._injection_parameters = _dict
            self._update_injection_efficiency = True
