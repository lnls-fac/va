
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
_light_speed = mathphys.constants.light_speed
UNDEF_VALUE = utils.UNDEF_VALUE
TRACK6D = True
calc_injection_eff = True
calc_timing_eff = True
orbit_unit = 1e9  #1e9m -> nm

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
        name_parts = self.model_module.device_names.split_name(pv_name)
        value = self._get_pv_dynamic(pv_name, name_parts)
        if value is None:
            value = self._get_pv_fake(pv_name, name_parts)
        if value is None:
            value = self._get_pv_static(pv_name, name_parts)
        if value is None:
            value = self._get_pv_timing(pv_name, name_parts)
        if value is None:
            value = self._get_pv_not_implemented(pv_name, name_parts)
        if value is None:
            raise Exception('response to ' + pv_name + ' not implemented in model get_pv')
        return value

    def _get_pv_dynamic(self, pv_name, name_parts):
        Discipline = name_parts['Discipline']
        Property   = name_parts['Property']
        if Discipline == 'DI' and Property == 'BbBCurrent':
            time_interval = pyaccel.optics.get_revolution_period(self._accelerator)
            currents = self._beam_charge.current(time_interval)
            currents_mA = [bunch_current / _u.mA for bunch_current in currents]
            return currents_mA
        elif Discipline == 'DI' and Property == 'Current':
            time_interval = pyaccel.optics.get_revolution_period(self._accelerator)
            currents = self._beam_charge.current(time_interval)
            currents_mA = [bunch_current / _u.mA for bunch_current in currents]
            return sum(currents_mA)
        elif Discipline == 'AP' and Property == 'BbBCurrLT':
            return [lifetime / _u.hour for lifetime in self._beam_charge.lifetime]
        elif Discipline == 'AP' and Property == 'CurrLT':
            return self._beam_charge.total_lifetime / _u.hour
        else:
            return None

    def _get_pv_static(self, pv_name, name_parts):
        Discipline = name_parts['Discipline']
        Device     = name_parts['Device']
        Device_name= name_parts['Device_name']
        Property   = name_parts['Property']
        if Discipline == 'PS':
            dev = self._power_supplies[Device_name]
            if Property.endswith('-SP'): return dev.current
            if Property.endswith('-RB'): return dev.current
        elif Discipline == 'PU':
            dev = self._pulsed_power_supplies[Device_name]
            if Property.endswith('-SP'): return dev.reference_value
            if Property.endswith('-RB'): return dev.current
        elif Discipline == 'DI':
            if Device == 'BPM':
                idx = self._get_elements_indices(pv_name)
                if Property == 'PosX-Mon':
                    if self._orbit is None: return [UNDEF_VALUE]*len(idx)
                    return orbit_unit*self._orbit[0,idx]
                elif Property == 'PosY-Mon':
                    if self._orbit is None: return [UNDEF_VALUE]*len(idx)
                    return orbit_unit*self._orbit[2,idx]
                return None
            elif Property == 'Freq1':
                return self._get_tune_component(Plane.horizontal)
            elif Property == 'Freq2':
                return self._get_tune_component(Plane.vertical)
            elif Property == 'Freq3':
                return self._get_tune_component(Plane.longitudinal)
            return None
        elif Discipline == 'RF':
            if Property == 'Freq':
                return pyaccel.optics.get_rf_frequency(self._accelerator)
            elif Property == 'Volt':
                idx = self._get_elements_indices(pv_name)
                return self._accelerator[idx[0]].voltage
            return None
        elif Discipline == 'AP':
            return UNDEF_VALUE
            if 'Chrom' in pv_name:
                return UNDEF_VALUE
            elif 'Chrom' in pv_name:
                return UNDEF_VALUE
            elif 'Emit' in pv_name:
                return UNDEF_VALUE
            elif 'BeamSz' in pv_name:
                return UNDEF_VALUE
            return None
        return None

    def _get_pv_fake(self, pv_name, name_parts):
        Discipline = name_parts['Discipline']
        if Discipline != 'FK': return None
        if 'ErrX' in pv_name:
            idx = self._get_elements_indices(pv_name)
            error = pyaccel.lattice.get_error_misalignment_x(self._accelerator, idx[0])
            return error
        if 'ErrY' in pv_name:
            idx = self._get_elements_indices(pv_name)
            error = pyaccel.lattice.get_error_misalignment_y(self._accelerator, idx[0])
            return error
        if 'ErrR' in pv_name:
            idx = self._get_elements_indices(pv_name)
            error = pyaccel.lattice.get_error_rotation_roll(self._accelerator, idx[0])
            return error
        if 'SaveFlatfile' in pv_name:
            return 0
        if 'Pos' in pv_name:
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

    def _get_pv_timing(self, pv_name, name_parts):
        Discipline = name_parts['Discipline']
        Device     = name_parts['Device']
        Property   = name_parts['Property']
        if Discipline == 'TI':
            if Property == 'Enbl' and pv_name in self._enabled2magnet.keys():
                magnet_name = self._enabled2magnet[pv_name]
                return self._pulsed_magnets[magnet_name].enabled
            elif Property == 'Delay' and pv_name in self._delay2magnet.keys():
                magnet_name = self._delay2magnet[pv_name]
                return self._pulsed_magnets[magnet_name].delay
            else:
                return None
        else:
            return None

    def _get_pv_not_implemented(self, pv_name, name_parts):
        Section    = name_parts['Section']
        Discipline = name_parts['Discipline']
        Device     = name_parts['Device']
        Property   = name_parts['Property']
        if Section == 'LI':
            if Device.startswith(('AccStr','ICT','Bun','Scrn','SHB')):
                return 1
        if Section == 'BO':
            if Device.startswith(('GSL','STDMOE','TuneS','Scrn',)):
                return 1
        if Section == 'SI':
            if Device.startswith(('BPME','GSL','BbBP','HBbBS','VBbBS','VTuneS',
                                  'HTuneS','HScrap','VScrap')):
                return 1
        elif Section.startswith('T'):
            if Device.startswith(('ICT','FCT','Scrn','HSlit','VSlit')):
                return 1


  # --- methods implementing response of model to set requests

    def _set_pv(self, pv_name, value):
        name_parts = self.model_module.device_names.split_name(pv_name)
        if self._set_pv_magnets(pv_name, value, name_parts): return
        if self._set_pv_rf(pv_name, value, name_parts): return
        if self._set_pv_fake(pv_name, value, name_parts): return
        if self._set_pv_timing(pv_name, value, name_parts): return

    def _set_pv_rf(self, pv_name, value, name_parts):
        Discipline = name_parts['Discipline']
        Property   = name_parts['Property']
        if not Discipline == 'RF': return None
        if Property == 'Volt':
            idx = self._get_elements_indices(pv_name)
            prev_value = self._accelerator[idx[0]].voltage
            if value != prev_value:
                self._accelerator[idx[0]].voltage = value
                self._state_deprecated = True
            return True
        elif Property == 'Freq':
            idx = self._get_elements_indices(pv_name)
            prev_value = self._accelerator[idx[0]].frequency
            if value != prev_value:
                self._accelerator[idx[0]].frequency = value
                self._state_deprecated = True
            return True
        return False

    def _set_pv_magnets(self, pv_name, value, name_parts):
        Discipline = name_parts['Discipline']
        Device_name= name_parts['Device_name']
        Property   = name_parts['Property']
        if Discipline == 'PS' and Property.endswith('-SP'):
            ps = self._power_supplies[Device_name]
            prev_value = ps.current
            if value != prev_value:
                ps.current = value
                self._state_deprecated = True
            return True
        elif Discipline == 'PU' and Property.endswith('-SP'):
            ps = self._pulsed_power_supplies[Device_name]
            prev_value = ps.reference_value
            if value != prev_value:
                ps.reference_value = value
                self._state_deprecated = True
            return True
        return False

    def _set_pv_fake(self, pv_name, value, name_parts):
        Discipline = name_parts['Discipline']
        if Discipline != 'FK': return None
        if 'ErrX' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorx = pyaccel.lattice.get_error_misalignment_x(self._accelerator, idx[0])
            if value != prev_errorx:
                pyaccel.lattice.set_error_misalignment_x(self._accelerator, idx, value)
                self._state_deprecated = True
            return True
        elif 'ErrY' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errory = pyaccel.lattice.get_error_misalignment_y(self._accelerator, idx[0])
            if value != prev_errory:
                pyaccel.lattice.set_error_misalignment_y(self._accelerator, idx, value)
                self._state_deprecated = True
            return True
        elif 'ErrR' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorr = pyaccel.lattice.get_error_rotation_roll(self._accelerator, idx[0])
            if value != prev_errorr:
                pyaccel.lattice.set_error_rotation_roll(self._accelerator, idx, value)
                self._state_deprecated = True
            return True
        elif 'SaveFlatfile' in pv_name:
            fname = 'flatfile_' + self.model_module.lattice_version + '.txt'
            pyaccel.lattice.write_flat_file(self._accelerator, fname)
            self._send_queue.put(('s', (pv_name, 0)))
            return True
        return None

    def _set_pv_timing(self, pv_name, value, name_parts):
        Discipline = name_parts['Discipline']
        Property   = name_parts['Property']
        if not Discipline == 'TI': return False
        if Property == 'Enbl' and pv_name in self._enabled2magnet.keys():
            magnet_name = self._enabled2magnet[pv_name]
            self._pulsed_magnets[magnet_name].enabled = value
            self._state_deprecated = True
            return True
        elif Property == 'Delay' and pv_name in self._delay2magnet.keys():
            magnet_name = self._delay2magnet[pv_name]
            self._pulsed_magnets[magnet_name].delay = value
            self._state_deprecated = True
            return True
        else:
            return False

   # --- auxiliary methods

    def _beam_inject(self, charge=None):
        if charge is None: return

        initial_charge = self._beam_charge.total_value
        self._beam_charge.inject(charge)

        final_charge = self._beam_charge.total_value
        if (initial_charge == 0) and (final_charge != initial_charge):
            self._state_changed = True

    def _beam_eject(self):
        charge = self._beam_charge.value
        self._beam_charge.dump()
        return charge

    def _init_sp_pv_values(self):
        utils.log('init', 'epics sp memory for %s pvs'%self.prefix)
        sp_pv_list = []
        for pv in self.pv_module.get_read_write_pvs() + self.pv_module.get_constant_pvs():
            value = self._get_pv(pv)
            sp_pv_list.append((pv,value))
        self._send_queue.put(('sp', sp_pv_list ))

    def _get_elements_indices(self, pv_name, flat=True):
        """Get flattened indices of element in the model"""
        Device_name = self.model_module.device_names.split_name(pv_name)['Device_name']
        data = self._all_pvs[Device_name]
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
        mod = self.model_module
        accelerator              = self._accelerator
        accelerator_data         = mod.accelerator_data
        magnet_names             = mod.get_magnet_names(accelerator)
        family_mapping           = mod.family_mapping
        excitation_curve_mapping = mod.device_names.get_excitation_curve_mapping(accelerator)
        pulse_curve_mapping      = mod.device_names.get_pulse_curve_mapping(accelerator)
        _, ps2magnet             = mod.device_names.get_magnet2power_supply_mapping(accelerator)
        self._magnet2delay, self._delay2magnet     = mod.device_names.get_magnet_delay_mapping(accelerator)
        self._magnet2enabled, self._enabled2magnet = mod.device_names.get_magnet_enabled_mapping(accelerator)

        self._magnets = dict()
        self._pulsed_magnets = dict()
        for magnet_name in magnet_names.keys():
            excitation_curve = excitation_curve_mapping[magnet_name]
            try:
                exc_curve_filename = os.path.join(accelerator_data['dirs']['excitation_curves'], excitation_curve)
            except:
                exc_curve_filename = os.path.join(accelerator_data['dirs']['excitation_curves'], 'not_found')

            family, indices = magnet_names[magnet_name].popitem()
            indices = indices[0]
            family_type = family_mapping[family]

            if family_type == 'dipole':
                if self.prefix == 'BO':
                    m = magnet.BoosterDipoleMagnet(accelerator, indices, exc_curve_filename)
                else:
                    m = magnet.NormalMagnet(accelerator, indices, exc_curve_filename)
            elif family_type  == 'pulsed_magnet':
                pulse_curve = pulse_curve_mapping[magnet_name]
                try:
                    pulse_curve_filename = os.path.join(accelerator_data['dirs']['pulse_curves'], pulse_curve)
                except:
                    pulse_curve_filename = os.path.join(accelerator_data['dirs']['pulse_curves'], 'not_found')
                m = magnet.PulsedMagnet(accelerator, indices, exc_curve_filename, pulse_curve_filename)
                self._pulsed_magnets[magnet_name] = m
            elif family_type == 'quadrupole':
                m = magnet.NormalMagnet(accelerator, indices, exc_curve_filename)
            elif family_type == 'sextupole':
                m = magnet.NormalMagnet(accelerator, indices, exc_curve_filename)
            elif family_type in ('slow_horizontal_corrector', 'fast_horizontal_corrector', 'horizontal_corrector'):
                m = magnet.NormalMagnet(accelerator, indices, exc_curve_filename)
            elif family_type in ('slow_vertical_corrector', 'fast_vertical_corrector', 'vertical_corrector'):
                m = magnet.SkewMagnet(accelerator, indices, exc_curve_filename)
            elif family_type == 'skew_quadrupole':
                m = magnet.SkewMagnet(accelerator, indices, exc_curve_filename)
            else:
                m = None

            if m is not None:
                self._magnets[magnet_name] = m

        # Set initial current values
        self._power_supplies = dict()
        self._pulsed_power_supplies = dict()
        for ps_name in ps2magnet.keys():
            magnets = set()
            for magnet_name in ps2magnet[ps_name]:
                if magnet_name in self._magnets:
                    magnets.add(self._magnets[magnet_name])
            if self.model_module.device_names.pvnaming_fam in ps_name:
                ps = power_supply.FamilyPowerSupply(magnets, model=self, ps_name=ps_name)
                self._power_supplies[ps_name] = ps

        # It is necessary to initalise all family power supplies before
        for ps_name in ps2magnet.keys():
            magnets = set()
            for magnet_name in ps2magnet[ps_name]:
                if magnet_name in self._magnets:
                    magnets.add(self._magnets[magnet_name])
            if not self.model_module.device_names.pvnaming_fam in ps_name:
                if 'PU' in ps_name:
                    ps = power_supply.PulsedMagnetPowerSupply(magnets, model=self, ps_name=ps_name)
                    self._pulsed_power_supplies[ps_name] = ps
                else:
                    ps = power_supply.IndividualPowerSupply(magnets, model=self, ps_name=ps_name)
                    self._power_supplies[ps_name] = ps

    def _get_sorted_pulsed_magnets(self):
        magnets_pos = []
        for magnet in self._pulsed_magnets.values():
            magnets_pos.append(magnet.length_to_egun)
        magnets_pos = sorted(magnets_pos)

        sorted_magnets = []
        for pos in magnets_pos:
            for magnet in self._pulsed_magnets.values():
                if magnet.length_to_egun == pos:
                    sorted_magnets.append(magnet)
        return sorted_magnets

    def _send_initialisation_sign(self):
        self._send_queue.put(('i', self.prefix))

    def _send_parameters_to_downstream_accelerator(self, _dict):
        prefix = self._downstream_accelerator_prefix
        self._send_queue.put(('p', (prefix, _dict)))

    def _get_parameters_from_upstream_accelerator(self, _dict):
        if 'pulsed_magnet_parameters' in _dict.keys():
            self._set_pulsed_magnets_parameters(**_dict['pulsed_magnet_parameters'])
        elif 'update_delays' in _dict.keys():
            self._update_pulsed_magnets_delays(_dict['update_delays'])
        elif 'injection_parameters' in _dict.keys():
            self._injection_parameters = _dict['injection_parameters']
            self._update_injection_efficiency = True
        elif 'injection_cycle' in _dict.keys():
            self._received_charge = True
            self._update_state()
            self._injection_cycle(**_dict['injection_cycle'])
            self._received_charge = False
