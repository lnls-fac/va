
import enum
import time
import numpy
import mathphys
import pyaccel

from siriuspy.namesys import SiriusPVName as _SiriusPVName

from va import area_structure
from va import magnet as _magnet
from va import power_supply
from va import beam_charge
from va import injection
from va import utils

_u = mathphys.units
_light_speed = mathphys.constants.light_speed
_meter_2_nm = _u.meter_2_mm**3 # model to control system orbit conversion
_undef_value = utils.UNDEF_VALUE

TRACK6D = True
CALC_INJECTION_EFF = True
CALC_TIMING_EFF = True


class Plane(enum.IntEnum):
    horizontal = 0
    vertical = 1
    longitudinal = 2


class AcceleratorModel(area_structure.AreaStructure):

    def __init__(self, **kwargs):
        self._injection_parameters = None
        # encapsulate DCCTs data structures within private methods,
        # just as for magnets and ps...
        self._dcct = {}
        super().__init__(**kwargs)
        self._reset('reset', 'model {}'.format(
            self.model_module.lattice_version))
        self._init_magnets_and_power_supplies()
        self._init_sp_pv_values()

    @property
    def accelerator(self):
        """."""
        return self._accelerator

    # --- methods implementing response of model to get requests

    def _get_pv(self, pv_name):
        parts = _SiriusPVName(pv_name)
        value = self._get_pv_dynamic(pv_name, parts)
        if value is None:
            value = self._get_pv_fake(pv_name, parts)
        if value is None:
            value = self._get_pv_static(pv_name, parts)
        if value is None:
            value = self._get_pv_timing(pv_name, parts)
        if value is None:
            value = self._get_pv_not_implemented(pv_name, parts)
        if value is None:
            utils.log(
                'warn',
                'response to '+pv_name+' not implemented in model get_pv',
                'yellow', a=['bold'])
            value = 0
            # raise Exception(
            #     'response to '+pv_name+' not implemented in model get_pv')
        return value

    def _get_pv_dynamic(self, pv_name, parts):
        if parts.dis == 'DI' and parts.propty == 'BbBCurrent-Mon':
            time_interval = pyaccel.optics.get_revolution_period(
                self._accelerator)
            currents = self._beam_charge.current(time_interval)
            currents_mA = [bunch_current / _u.mA for bunch_current in currents]
            return currents_mA
        elif parts.dis == 'DI' and parts.propty == 'Current-Mon':
            time_interval = pyaccel.optics.get_revolution_period(
                self._accelerator)
            currents = self._beam_charge.current(time_interval)
            currents_mA = [bunch_current / _u.mA for bunch_current in currents]
            return sum(currents_mA)
        elif parts.dis == 'AP' and parts.propty == 'BbBCurrLT-Mon':
            return [lifetime for lifetime in self._beam_charge.lifetime]
            # return [lifetime / _u.hour for lifetime in self._beam_charge.lifetime]
        elif parts.dis == 'AP' and parts.propty == 'CurrLT-Mon':
            return self._beam_charge.total_lifetime
            # return self._beam_charge.total_lifetime / _u.hour
        elif parts.dis == 'PS' and parts.propty == 'TimestampUpdate-Mon':
            return time.time()
        else:
            return None

    def _get_pv_static(self, pv_name, parts):
        if parts.dis in ('PS', 'PU'):
            if parts.dis == 'PS':
                dev = self._power_supplies[parts.device_name]
            elif parts.dis == 'PU':
                dev = self._pulsed_power_supplies[parts.device_name]
            value = dev.get_pv(pv_name, parts)
            if value is not None: return value
        elif parts.dis == 'DI':
            if parts.dev == 'BPM':
                idx = self._get_elements_indices(pv_name)
                if parts.propty == 'PosX-Mon':
                    if self._orbit is None:
                        return _undef_value
                    return _meter_2_nm*self._orbit[0, idx]
                elif parts.propty == 'PosY-Mon':
                    if self._orbit is None:
                        return _undef_value
                    return _meter_2_nm*self._orbit[2, idx]
                return None
            elif parts.dev in ('SlitH', 'SlitV'):
                return 0.0
            elif parts.propty == 'HwFlt-Mon':
                try:
                    dcct = self._dcct[parts.device_name]
                except:
                    dcct = self._dcct[parts.device_name] = {'HwFlt':0, 'CurrThold':0.0}
                return dcct['HwFlt']
            elif parts.propty == 'CurrThold':
                try:
                    dcct = self._dcct[parts.device_name]
                except:
                    dcct = self._dcct[parts.device_name] = {'HwFlt':0, 'CurrThold':0.0}
                return dcct['CurrThold']
            elif parts.propty == 'Freq1-Mon':
                return self._get_tune_component(Plane.horizontal)
            elif parts.propty == 'Freq2-Mon':
                return self._get_tune_component(Plane.vertical)
            elif parts.propty == 'Freq3-Mon':
                return self._get_tune_component(Plane.longitudinal)
            return None
        elif parts.dis == 'RF':
            if parts.propty in ('Freq-SP','Freq-RB'):
                return pyaccel.optics.get_rf_frequency(self._accelerator)
            elif parts.propty in ('Volt-SP', 'Volt-RB'):
                idx = self._get_elements_indices(pv_name)
                return self._accelerator[idx[0]].voltage
            return None
        elif parts.dis == 'AP':
            return _undef_value
            if 'Chrom' in pv_name:
                return _undef_value
            elif 'Chrom' in pv_name:
                return _undef_value
            elif 'Emit' in pv_name:
                return _undef_value
            elif 'BeamSz' in pv_name:
                return _undef_value
            return None
        elif parts.dis == 'MO':
            if parts.dev == 'Lattice':
                if parts.propty == 'BPMPos-Cte':
                    indices = self._get_elements_indices('BPM', flat=False)
                    if isinstance(indices[0], int):
                        pos = pyaccel.lattice.find_spos(
                            self._accelerator, indices)
                    else:
                        pos = [pyaccel.lattice.find_spos(
                            self._accelerator, idx[0]) for idx in indices]
                    start = pyaccel.lattice.find_indices(
                        self._accelerator, 'fam_name', 'start')[0]
                    start_spos = pyaccel.lattice.find_spos(
                        self._accelerator, start)
                    pos = (pos-start_spos) % pyaccel.lattice.length(
                        self._accelerator)
                    return pos
        return None

    def _get_pv_fake(self, pv_name, parts):
        if parts.dis != 'FK':
            return None
        if 'ErrX' in pv_name:
            idx = self._get_elements_indices(pv_name)
            error = pyaccel.lattice.get_error_misalignment_x(
                self._accelerator, idx[0])
            return error
        if 'ErrY' in pv_name:
            idx = self._get_elements_indices(pv_name)
            error = pyaccel.lattice.get_error_misalignment_y(
                self._accelerator, idx[0])
            return error
        if 'ErrR' in pv_name:
            idx = self._get_elements_indices(pv_name)
            error = pyaccel.lattice.get_error_rotation_roll(
                self._accelerator, idx[0])
            return error
        if 'SaveFlatfile' in pv_name:
            return 0
        if 'Pos' in pv_name:
            indices = self._get_elements_indices(pv_name, flat=False)
            if isinstance(indices[0], int):
                pos = pyaccel.lattice.find_spos(self._accelerator, indices)
            else:
                pos = [
                    pyaccel.lattice.find_spos(self._accelerator, idx[0])
                    for idx in indices]
            start = pyaccel.lattice.find_indices(
                self._accelerator, 'fam_name', 'start')[0]
            start_spos = pyaccel.lattice.find_spos(self._accelerator, start)
            pos = (pos-start_spos) % pyaccel.lattice.length(self._accelerator)
            return pos
        else:
            return None

    def _get_pv_timing(self, pv_name, parts):

        if not parts.dis == 'TI':
            return None
        if parts.propty not in ('Enbl-SP', 'Enbl-RB', 'Delay-SP', 'Delay-RB'):
            return None

        pvname = parts.substitute(propty_suffix='RB')
        if pvname in self._enabled2magnet:
            magnet_name = self._enabled2magnet[pvname]
            return self._pulsed_magnets[magnet_name].enabled
        elif pvname in self._delay2magnet:
            magnet_name = self._delay2magnet[pvname]
            return self._pulsed_magnets[magnet_name].delay
        else:
            return None

    def _get_pv_not_implemented(self, pv_name, parts):
        if parts.sec == 'LI':
            if parts.dev.startswith(('AccStr','ICT','Bun','Scrn','SHB')):
                return 1
            if pv_name.endswith('-Cmd'):
                return 1
        if parts.sec == 'BO':
            if parts.dev.startswith(('GSL','STDMOE','TuneS','Scrn',)):
                return 1
        if parts.sec == 'SI':
            if parts.dev.startswith(('BPME','GSL','BbBP','HBbBS','VBbBS','VTuneS',
                                  'HTuneS','HScrap','VScrap')):
                return 1
        elif parts.sec.startswith('T'):
            if parts.dev.startswith(('ICT','FCT','Scrn','HSlit','VSlit')):
                return 1

    # --- methods implementing response of model to set requests

    def _set_pv(self, pv_name, value):
        parts = _SiriusPVName(pv_name)
        if self._set_pv_vaca(pv_name, value, parts):
            return
        if self._set_pv_magnets(pv_name, value, parts):
            return
        if self._set_pv_di(pv_name, value, parts):
            return
        if self._set_pv_rf(pv_name, value, parts):
            return
        if self._set_pv_fake(pv_name, value, parts):
            return
        if self._set_pv_timing(pv_name, value, parts):
            return

    def _set_pv_vaca(self, pv_name, value, parts):
        if parts.dis == 'VA':
            if parts.propty == 'BeamCurrentAdd-SP':
                time_interval = pyaccel.optics.get_revolution_period(
                    self._accelerator)
                nr_bunches = self._beam_charge.nr_bunches
                charge_delta = _u.mA * (value/nr_bunches) * time_interval * numpy.ones(nr_bunches)
                self._beam_inject(charge=charge_delta)
            elif parts.propty == 'BeamCurrentDump-Cmd':
                self._beam_eject()

    def _set_pv_di(self, pv_name, value, parts):
        if parts.dis == 'DI':
            if parts.propty == 'CurrThold':
                prev_value = self._dcct[parts.device_name]['CurrThold']
                if value != prev_value:
                    if value < 0:
                        self._others_queue['driver'].put(('s', (pv_name, prev_value)))
                    else:
                        self._dcct[parts.device_name]['CurrThold'] = value
                    return True
        return False

    def _set_pv_rf(self, pv_name, value, parts):
        if not parts.dis == 'RF': return None
        if parts.propty == 'Volt-SP':
            idx = self._get_elements_indices(pv_name)
            prev_value = self._accelerator[idx[0]].voltage
            if value != prev_value:
                self._accelerator[idx[0]].voltage = value
                self._others_queue['driver'].put(('s', (pv_name.replace('Volt-SP','Volt-RB'), value))) # It would be cleaner if this were implemented inside PS object!
                self._state_deprecated = True
            return True
        elif parts.propty == 'Freq-SP':
            idx = self._get_elements_indices(pv_name)
            prev_value = self._accelerator[idx[0]].frequency
            if value != prev_value:
                self._accelerator[idx[0]].frequency = value
                self._others_queue['driver'].put(('s', (pv_name.replace('Freq-SP','Freq-RB'), value))) # It would be cleaner if this were implemented inside PS object!
                self._state_deprecated = True
            return True
        return False

    def _set_pv_magnets(self, pv_name, value, parts):
        if parts.dis in ('PS','PU'):
            if parts.dis == 'PS':   dev = self._power_supplies[parts.device_name]
            elif parts.dis == 'PU': dev = self._pulsed_power_supplies[parts.device_name]
            deprecated_pvs = dev.set_pv(pv_name, value, parts)
            if deprecated_pvs:
                for pvname,value in deprecated_pvs.items():
                    self._others_queue['driver'].put(('s', (pvname, value)))
                self._state_deprecated = True
                return True
        return False

    def _set_pv_fake(self, pv_name, value, parts):
        if parts.dis != 'FK': return None
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
            self._others_queue['driver'].put(('s', (pv_name, 0)))
            return True
        return None

    def _set_pv_timing(self, pv_name, value, parts):
        if not parts.dis == 'TI': return False
        if parts.propty == 'Enbl-SP' and pv_name in self._enabled2magnet.keys():
            magnet_name = self._enabled2magnet[pv_name]
            self._pulsed_magnets[magnet_name].enabled = value
            self._state_deprecated = True
            return True
        elif parts.propty == 'Delay-SP' and pv_name in self._delay2magnet.keys():
            magnet_name = self._delay2magnet[pv_name]
            self._pulsed_magnets[magnet_name].delay = value
            self._state_deprecated = True
            return True
        else:
            return False

    # --- auxiliary methods

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        if self._beam_charge:
            self._beam_charge.dump()
        self._orbit = None  # means no closed orbit
        self._twiss = None  # means no optics

    def _beam_inject(self, charge=None):
        if charge is None:
            return

        initial_charge = self._beam_charge.total_value
        self._beam_charge.inject(charge)

        final_charge = self._beam_charge.total_value
        if (initial_charge == 0) and (final_charge != initial_charge):
            self._state_changed = True

    def _beam_eject(self):
        charge = self._beam_charge.value
        self._beam_charge.dump()
        return charge

    def _get_elements_indices(self, pv_name, flat=True):
        """Get flattened indices of element in the model"""
        parts = _SiriusPVName(pv_name)
        data = self._all_pvs[parts.device_name]
        indices = []
        for key in data.keys():
            if flat:
                idx = numpy.array(data[key]).flatten()
            else:
                idx = data[key]
            indices.extend(idx)
        return indices

    def _set_vacuum_chamber(self):
        self._hmin = numpy.array(pyaccel.lattice.get_attribute(
            self._accelerator, 'hmin'))
        self._hmax = numpy.array(pyaccel.lattice.get_attribute(
            self._accelerator, 'hmax'))
        self._vmin = numpy.array(pyaccel.lattice.get_attribute(
            self._accelerator, 'vmin'))
        self._vmax = numpy.array(pyaccel.lattice.get_attribute(
            self._accelerator, 'vmax'))

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
        marker.hmin = self._accelerator[-1].hmin
        marker.hmax = self._accelerator[-1].hmax
        marker.vmin = self._accelerator[-1].vmin
        marker.vmax = self._accelerator[-1].vmax
        self._accelerator.append(marker)

    def _init_magnets_and_power_supplies(self):
        t0 = time.time()
        utils.log('init',
            '{}: initialising magnet and power supplies'.format(self.prefix), 'green')
        accelerator = self._accelerator
        magnet_names = self.device_names.get_magnet_names(accelerator)
        family_mapping = self.model_module.family_mapping
        excit_curv_polarity_map = \
            self.device_names.get_excitation_curve_mapping(accelerator)
        pulse_curve_mapping = self.device_names.get_pulse_curve_mapping(
            accelerator)
        _, ps2magnet = self.device_names.get_magnet2power_supply_mapping(
            accelerator)
        self._magnet2delay, self._delay2magnet = \
            self.device_names.get_magnet_delay_mapping(accelerator)
        self._magnet2enabled, self._enabled2magnet = \
            self.device_names.get_magnet_enabled_mapping(accelerator)

        # create magnet objects
        self._magnets = dict()
        self._pulsed_magnets = dict()
        for magnet_name in magnet_names.keys():
            if '-Fam' in magnet_name:
                continue
            excitation_curve, polarity = excit_curv_polarity_map[magnet_name]
            family, indices = magnet_names[magnet_name].popitem()
            family_type = family_mapping[family]

            if family_type == 'dipole':
                if self.prefix == 'BO':
                    m = _magnet.BoosterDipoleMagnet(
                        accelerator, indices, excitation_curve, polarity)
                else:
                    m = _magnet.NormalMagnet(
                        accelerator, indices, excitation_curve, polarity)
            elif family_type == 'pulsed_magnet':
                pulse_curve = pulse_curve_mapping[magnet_name]
                try:
                    # pulse_curve_filename = os.path.join(
                    #     self._pulse_curves_dir, pulse_curve)
                    pulse_curve_filename = pulse_curve
                except:
                    # pulse_curve_filename = os.path.join(
                    #     self._pulse_curves_dir, 'not_found')
                    pulse_curve_filename = pulse_curve
                m = _magnet.PulsedMagnet(
                    accelerator, indices, excitation_curve, polarity,
                    pulse_curve_filename)
                self._pulsed_magnets[magnet_name] = m
            elif family_type == 'quadrupole':
                m = _magnet.NormalMagnet(
                    accelerator, indices, excitation_curve, polarity)
            elif family_type == 'sextupole':
                m = _magnet.NormalMagnet(
                    accelerator, indices, excitation_curve, polarity)
            elif family_type in (
                    'slow_horizontal_corrector', 'fast_horizontal_corrector',
                    'horizontal_corrector'):
                m = _magnet.NormalMagnet(
                    accelerator, indices, excitation_curve, polarity)
            elif family_type in (
                'slow_vertical_corrector', 'fast_vertical_corrector',
                'vertical_corrector'):
                m = _magnet.SkewMagnet(
                    accelerator, indices, excitation_curve, polarity)
            elif family_type == 'skew_quadrupole':
                m = _magnet.SkewMagnet(
                    accelerator, indices, excitation_curve, polarity)
            elif family_type in ('solenoid','magnetic_lens'):
                m = _magnet.NormalMagnet(
                    accelerator, indices, excitation_curve, polarity)
            else:
                m = None

            if m is not None:
                self._magnets[magnet_name] = m

        # create power supply objetcs
        self._power_supplies = dict()
        self._pulsed_power_supplies = dict()
        for psname in ps2magnet.keys():
            magnets = set()
            for magnet_name in ps2magnet[psname]:
                if magnet_name in self._magnets:
                    magnets.add(self._magnets[magnet_name])
            if self.device_names.pvnaming_fam in psname:
                ps = power_supply.FamilyPowerSupply(
                    magnets, model=self, psname=psname)
                ps.initialise()
                self._power_supplies[psname] = ps

        # It is necessary to initalise all family power supplies before
        for psname in ps2magnet.keys():
            magnets = set()
            for magnet_name in ps2magnet[psname]:
                if magnet_name in self._magnets:
                    magnets.add(self._magnets[magnet_name])
            if self.device_names.pvnaming_fam not in psname:
                if 'PU' in psname:
                    ps = power_supply.PulsedMagnetPowerSupply(
                        magnets, model=self, psname=psname)
                    ps.initialise()
                    self._pulsed_power_supplies[psname] = ps
                else:
                    ps = power_supply.IndividualPowerSupply(
                        magnets, model=self, psname=psname)
                    ps.initialise()
                    self._power_supplies[psname] = ps

        utils.log('init',
            '{}: magnet and power supplies initialised ({:.0f} ms)'.format(self.prefix, 1e3*(time.time() - t0)), 'green')

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


class LinacModel(AcceleratorModel):

    def __init__(self, **kwargs):
        self._injection_bunch = 1
        super().__init__(**kwargs)
        self._set_pulsed_magnets_parameters()
        self._send_initialisation_sign()

    # --- methods implementing response of model to get requests

    def _get_pv_fake(self, pv_name, parts):
        if parts.dis == 'FK' and 'Mode' in pv_name:
            return self._single_bunch_mode
        return super()._get_pv_fake(pv_name, parts)

    def _get_pv_timing(self, pv_name, parts):
        value = super()._get_pv_timing(pv_name, parts)
        if value is not None:
            return value

        if not parts.dis == 'TI':
            return None
        if parts.dev == 'EGun':
            if parts.propty in ('Enbl-SP', 'Enbl-RB'):
                return self._egun_enabled
            elif parts.propty in ('Delay-SP', 'Delay-RB'):
                if not hasattr(self, '_egun_delay'):
                    return _undef_value
                return self._egun_delay
        else:
            return None

    # --- methods implementing response of model to set requests

    def _set_pv_fake(self, pv_name, value, parts):
        if parts.dis == 'FK' and 'Mode' in pv_name:
            self._single_bunch_mode = value
            return True
        return super()._set_pv_fake(pv_name, value, parts)

    def _set_pv_timing(self, pv_name, value, parts):
        if super()._set_pv_timing(pv_name, value, parts): return

        if not parts.dis == 'TI':
            return False
        if parts.dev == 'EGun':
            if parts.propty == 'Enbl-SP':
                self._egun_enabled = value
            elif parts.propty == 'Delay-SP':
                self._egun_delay = value
            else: return False
            return True
        return False

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._state_deprecated or self._update_injection_efficiency:
            self._calc_transport_efficiency()
            self._state_deprecated = False
            self._update_injection_efficiency = False
            self._state_changed = True

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._accelerator, *_ = self.model_module.create_accelerator()
        self._lattice_length = pyaccel.lattice.length(self._accelerator)
        self._append_marker()
        self._all_pvs = self.device_names.get_device_names(self._accelerator)
        #self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)
        self._set_vacuum_chamber()
        self._state_deprecated = True
        self._update_state()
        self._egun_enabled = 1
        self._egun_delay = 0
        self._single_bunch_mode = 0

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        super()._beam_dump(message1, message2, c, a)
        self._injection_efficiency = 1.0
        self._ejection_efficiency  = 1.0

    # --- auxiliary methods

    def _calc_transport_efficiency(self):
        inj_params =  {
            'emittance': self._emittance,
            'energy_spread': self._energy_spread,
            'global_coupling': self._global_coupling,
            'init_twiss': self._twiss_at_match}

        _dict = {}
        _dict.update(inj_params)
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())
    
        idx = pyaccel.lattice.find_indices(self._accelerator,'fam_name','twiss_at_match')
        _dict['accelerator'] = self._accelerator[idx:]
        loss_fraction, self._twiss, self._m66 = \
            injection.calc_charge_loss_fraction_in_line(self, **_dict)
        self._transport_efficiency = 1.0 - loss_fraction
        self._log('calc', '{}: transport efficiency {:.2f} %'.format(
            self.model_module.lattice_version, 100*self._transport_efficiency))

        if self._twiss is not None:
            self._orbit = self._twiss.co

        args_dict = {}
        # picklable object
        args_dict['init_twiss'] = self._twiss[-1].make_dict()
        args_dict.update(inj_params)
        self._send_parameters_to_other_area_structure(
            prefix=self._downstream_accelerator_prefix,
            _dict = {'injection_parameters': args_dict})

    def _set_pulsed_magnets_parameters(self):
        _dict = { 'pulsed_magnet_parameters' : {
            'total_length': self._accelerator.length,
            'magnet_pos': 0, 'nominal_delays': {'EGun' : self._egun_delay}}
        }
        self._send_parameters_to_other_area_structure(
            prefix=self._downstream_accelerator_prefix, _dict=_dict)

    def _update_pulsed_magnets_delays(self, delays):
        for magnet_name, delay in delays.items():
            if 'EGun' in magnet_name:
                self._egun_delay = delay
        self._update_delay_pvs_in_epics_memory()
        self._send_parameters_to_other_area_structure(
            prefix=self._downstream_accelerator_prefix,
            _dict={'update_delays' : delays})
        self._send_initialisation_sign()

    def _update_delay_pvs_in_epics_memory(self):
        pv_name = self.device_names.join_name(
            '01', 'TI', 'EGun', proper='Delay-SP')
        self._others_queue['driver'].put(('s', (pv_name, self._egun_delay)))

    def _injection_cycle(self, **kwargs):

        if self._egun_enabled:
            if self._single_bunch_mode:
                charge = [self._single_bunch_charge]
            else:
                charge = [self._multi_bunch_charge/self.nr_bunches]*self.nr_bunches
        else:
            self._log(message1='cycle', message2='-- '+self.prefix+' --')
            self._log(
                message1='cycle',
                message2='electron gun providing charge: {0:.5f} nC'.format(
                    0.0))
            self._log(message1='cycle', message2='Stoping injection')
            return
        self._log(message1='cycle', message2='-- '+self.prefix+' --')
        self._log(
            message1='cycle',
            message2='electron gun providing charge: {0:.5f} nC'.format(
                sum(charge)*1e9))
        self._log(
            message1='cycle',
            message2='beam injection in {0:s}: {1:.5f} nC'.format(
                self.prefix, sum(charge)*1e9))

        charge_time = [(kwargs['injection_bunch'] + i)*kwargs['bunch_separation']+self._egun_delay for i in range(len(charge))]

        if CALC_INJECTION_EFF and not self.simulate_only_orbit:
            efficiency = self._transport_efficiency if self._transport_efficiency is not None else 0
            charge = [bunch_charge * efficiency for bunch_charge in charge]
            self._log(message1='cycle', message2='beam transport at {0:s}: {1:.4f}% efficiency'.format(self.prefix, 100*efficiency))

        kwargs['charge']      =  charge
        kwargs['charge_time'] = charge_time
        self._send_parameters_to_other_area_structure(prefix = self._downstream_accelerator_prefix,
                                                      _dict  = {'injection_cycle' : kwargs})


class TLineModel(AcceleratorModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._send_initialisation_sign()

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._state_deprecated or self._update_injection_efficiency:
            self._calc_transport_efficiency()
            self._state_deprecated = False
            self._update_injection_efficiency = False
            self._state_changed = True

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._accelerator, *_ = self.model_module.create_accelerator()
        self._lattice_length = pyaccel.lattice.length(self._accelerator)
        self._append_marker()
        self._all_pvs = self.device_names.get_device_names(self._accelerator)
        #self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)
        self._set_vacuum_chamber()
        self._state_deprecated = True
        self._update_state()

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        super()._beam_dump(message1, message2, c, a)
        self._injection_parameters = None
        self._transport_efficiency = None

    # --- auxiliary methods

    def _set_pulsed_magnets_parameters(self, **kwargs):
        if 'total_length' in kwargs:
            prev_total_length = kwargs['total_length']
        if 'magnet_pos' in kwargs:
            prev_magnet_pos = kwargs['magnet_pos']
        if 'nominal_delays' in kwargs:
            nominal_delays = kwargs['nominal_delays']

        # for ps in self._pulsed_power_supplies.values():
        #     ps.pwrstate_sel = 0

        magnets_pos = dict()
        for magnet_name, magnet in self._pulsed_magnets.items():
            magnet_pos = prev_total_length + magnet.length_to_inj_point
            magnet.length_to_egun = magnet_pos
            magnets_pos[magnet_name] = magnet_pos
        sorted_magnets_pos = sorted(magnets_pos.items(), key=lambda x: x[1])

        for i in range(len(sorted_magnets_pos)):
            magnet_name, magnet_pos = sorted_magnets_pos[i]
            magnet = self._pulsed_magnets[magnet_name]
            magnet.length_to_prev_pulsed_magnet = magnet_pos - prev_magnet_pos
            nominal_delays[magnet_name] = magnet.delay
            prev_magnet_pos = magnet_pos

        total_length = prev_total_length + self._accelerator.length

        _dict = { 'pulsed_magnet_parameters' : {
            'total_length'     : total_length,
            'magnet_pos'       : magnet_pos,
            'nominal_delays'   : nominal_delays,}
        }
        self._send_parameters_to_other_area_structure(prefix = self._downstream_accelerator_prefix,
                                                      _dict  = _dict)

    def _update_pulsed_magnets_delays(self, delays):
        for magnet_name, delay in delays.items():
            if magnet_name in self._pulsed_magnets.keys():
                self._pulsed_magnets[magnet_name].delay = delay
        self._update_delay_pvs_in_epics_memory()
        self._send_parameters_to_other_area_structure(prefix = self._downstream_accelerator_prefix,
                                                      _dict  = {'update_delays' : delays})

    def _update_delay_pvs_in_epics_memory(self):
        for magnet_name, magnet in self._pulsed_magnets.items():
            pv_name = self._magnet2delay[magnet_name]
            value = magnet.delay
            self._others_queue['driver'].put(('s', (pv_name, value)))

    def _calc_transport_efficiency(self):
        if self._injection_parameters is None:
            return

        _dict = {}

        _dict.update(self._injection_parameters)
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())

        # for ps in self._pulsed_power_supplies.values():
        #     ps.pwrstate_sel = 1

        loss_fraction, self._twiss, self._m66 = injection.calc_charge_loss_fraction_in_line(self, **_dict)
        self._transport_efficiency = 1.0 - loss_fraction
        self._log('calc', '{}: transport efficiency {:.2f} %'.format(
            self.model_module.lattice_version, 100*self._transport_efficiency))
        if self._twiss is not None:
            self._orbit = self._twiss.co

        # for ps in self._pulsed_power_supplies.values():
        #     ps.pwrstate_sel = 0

        args_dict = {}
        args_dict.update(self._injection_parameters)
        args_dict['init_twiss'] = self._twiss[-1].make_dict() # picklable object
        self._send_parameters_to_other_area_structure(
            prefix=self._downstream_accelerator_prefix,
            _dict={'injection_parameters': args_dict})

    def _injection_cycle(self, **kwargs):
        charge = kwargs['charge']
        charge_time = kwargs['charge_time']

        self._log(message1='cycle', message2='-- '+self.prefix+' --')
        self._log(
            message1='cycle',
            message2='beam injection in {:s}: {:.5f} nC'.format(
                self.prefix, sum(charge)*1e9))

        if CALC_TIMING_EFF and not self.simulate_only_orbit:
            prev_charge = sum(charge)
            for magnet in self._get_sorted_pulsed_magnets():
                charge, charge_time = magnet.pulsed_magnet_pass(
                    charge, charge_time, kwargs['master_delay'])
            efficiency = (sum(charge)/prev_charge) if prev_charge != 0 else 0
            self._log(message1='cycle', message2='pulsed magnets in {:s}: {:.4f}% efficiency'.format(self.prefix, 100*efficiency))

        if CALC_INJECTION_EFF and not self.simulate_only_orbit:
            efficiency = self._transport_efficiency if self._transport_efficiency is not None else 0
            if 'ejection_efficiency' in kwargs: efficiency = efficiency*kwargs['ejection_efficiency']
            charge = [bunch_charge * efficiency for bunch_charge in charge]
            self._log(message1='cycle', message2='beam transport at {:s}: {:.4f}% efficiency'.format(self.prefix, 100*efficiency))

        kwargs['charge'] = charge   
        kwargs['charge_time'] = charge_time
        self._send_parameters_to_other_area_structure(
            prefix = self._downstream_accelerator_prefix,
            _dict  = {'injection_cycle' : kwargs})


class RingModel(AcceleratorModel):
    """Ring models."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._send_initialisation_sign()

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        super()._beam_dump(message1, message2, c, a)
        self._m66 = None
        self._tunes = None
        self._transfer_matrices = None
        self._lifetime = None
        self._injection_efficiency = None

    def _calc_closed_orbit(self):
        """Calculate closed orbit when there is beam."""

        latver = self.model_module.lattice_version

        try:
            self._log('calc', '{}: closed orbit'.format(latver))
            if TRACK6D:
                self._orbit = pyaccel.tracking.findorbit6(self._accelerator, indices='open')
            else:
                self._orbit = numpy.zeros((6, len(self._accelerator)))
                self._orbit[:4, :] = pyaccel.tracking.findorbit4(self._accelerator, indices='open')
        except pyaccel.tracking.TrackingException:
            # beam is lost
            self._beam_dump('panic', '{}: closed orbit does not exist and beam is lost'.format(latver), c='red')

    def _calc_linear_optics(self):
        """Calculate linear optics when there is beam."""

        latver = self.model_module.lattice_version

        if self._orbit is None:
            return

        try:
            self._log('calc', '{}: linear optics'.format(latver))
            self._twiss, self._m66 = \
                pyaccel.optics.calc_twiss(self._accelerator, fixed_point=self._orbit[:, 0])
            self._tunes = pyaccel.optics.get_frac_tunes(m1turn=self._m66)
        # Beam is lost
        except (
            ValueError,
            numpy.linalg.linalg.LinAlgError,
            pyaccel.optics.OpticsException,
            pyaccel.tracking.TrackingException,
            ) as err:
            self._beam_dump('panic',
                '{}: unstable linear optics and beam is lost ({})'.format(latver, str(err)), c='red')

    def _calc_equilibrium_parameters(self):
        """Calculate equilibrium parameters."""

        latver = self.model_module.lattice_version

        if self._m66 is None:
            return

        try:
            self._log('calc', '{}: equilibrium parameters'.format(latver))
            self._lifetime =  pyaccel.lifetime.Lifetime(self._accelerator)
        except Exception as err:
            self._beam_dump('panic',
                '{}: unable to calc equilibrium parameters and beam is lost ({})'.format(latver, str(err)), c='red')

    def _calc_lifetimes(self):
        latver = self.model_module.lattice_version

        if self._lifetime is None or self._beam_charge is None: return

        time_interval = pyaccel.optics.get_revolution_period(self._accelerator)
        charge_total = self._beam_charge.total_value
        current_total = charge_total / time_interval
        self._lifetime.curr_per_bunch = current_total / self._beam_charge.nr_bunches
        self._beam_charge.set_lifetimes(self._lifetime)
        le, li, lq, tc = \
            self._beam_charge.get_lifetimes()
        s2h = 1/3600
        tlossrate = tc * charge_total
        lt = 1/tlossrate if tlossrate > 0 else float('inf')
        ltot = self._beam_charge.total_lifetime
        strf = '{}: beam lifetimes [h] (e:{:.2f}, i:{:.2f}, q:{:.2f}, t:{:.2f}, tot:{:.2f})'
        self._log('calc', strf.format(latver, le*s2h, li*s2h, lq*s2h, lt*s2h, ltot*s2h))


class BoosterModel(RingModel):

    # --- methods implementing response of model to get requests

    def _get_pv_timing(self, pv_name, parts):
        value = super()._get_pv_timing(pv_name, parts)
        if value is not None: return value

        if parts.dis == 'TI':
            if 'RampPS:Enbl' in pv_name:
                return self._rampps_enabled
            elif 'RampPS:Delay' in pv_name:
                return self._rampps_delay
            else:
                return None
        else:
            return None

    # --- methods implementing response of model to set requests

    def _set_pv_timing(self, pv_name, value, parts):
        if super()._set_pv_timing(pv_name, value, parts): return

        if parts.dis == 'TI':
            if 'RampPS:Enbl-SP' in pv_name:
                self._rampps_enabled = value
                return True
            elif 'RampPS:Delay-SP' in pv_name:
                self._rampps_delay = value
                return True
            else:
                return False
        else:
            return False

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._state_deprecated:
            self._calc_closed_orbit()
            if not self.simulate_only_orbit:
                self._calc_linear_optics()
                self._calc_equilibrium_parameters()
                self._calc_lifetimes()
            self._update_injection_efficiency = True
            self._update_ejection_efficiency  = True
            self._state_changed = True
            self._state_deprecated = False
        self._calc_efficiencies()

    def _calc_efficiencies(self):
        if self._lifetime is None:
            self._update_injection_efficiency = False
            self._update_ejection_efficiency  = False
            return

        # Calculate injection efficiency
        if self._update_injection_efficiency:# and (self._received_charge or self._injection_efficiency is None):
            self._update_injection_efficiency = False
            self._calc_injection_efficiency()

        # Calculate ejection efficiency
        if self._update_ejection_efficiency:# and (self._received_charge or self._ejection_efficiency is None):
            self._update_ejection_efficiency = False
            self._calc_ejection_efficiency()

    def _reset(self, message1='reset', message2='', c='white', a=None):
        # Create beam charge object
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)

        # Shift accelerator to start in the injection point
        self._accelerator  = self.model_module.create_accelerator(energy=self.init_energy)
        self._lattice_length = pyaccel.lattice.length(self._accelerator)
        if not hasattr(self, '_injection_point_label'):
            self._others_queue['driver'].put(('a', 'injection point label for ' + self.model_module.lattice_version + ' not defined!'))
        else:
            injection_point    = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', self._injection_point_label)[0]
            if not injection_point:
                self._others_queue['driver'].put(('a', 'injection point label "' + self._injection_point_label + '" not found in ' + self.model_module.lattice_version))
            else:
                self._accelerator  = pyaccel.lattice.shift(self._accelerator, start = injection_point)

        # Append marker to accelerator
        self._append_marker()
        self._extraction_point = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', self._extraction_point_label)[0]

        # Create record names dictionary
        self._all_pvs = self.device_names.get_device_names(self._accelerator)
        #self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))

        # Set radiation and cavity on
        if TRACK6D:
            pyaccel.tracking.set6dtracking(self._accelerator)

        self._set_vacuum_chamber()
        self._rampps_enabled = 1
        self._rampps_delay = 0
        self._state_deprecated = True
        self._update_state()

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        super()._beam_dump(message1, message2, c, a)
        self._ejection_efficiency  = None

    # --- auxiliary methods

    def _set_pulsed_magnets_parameters(self, **kwargs):
        if 'total_length' in kwargs:
            prev_total_length = kwargs['total_length']
        if 'magnet_pos' in kwargs:
            prev_magnet_pos = kwargs['magnet_pos']
        if 'nominal_delays' in kwargs:
            nominal_delays = kwargs['nominal_delays']

        # for ps in self._pulsed_power_supplies.values():
        #     ps.pwrstate_sel = 0

        one_turn_time = self._accelerator.length/_light_speed
        ramp_length =  int(self._ramp_interval/one_turn_time)*self._accelerator.length

        magnets_pos = dict()
        for magnet_name, magnet in self._pulsed_magnets.items():
            magnet_pos = prev_total_length + magnet.length_to_inj_point
            if 'Eje' in magnet_name: magnet_pos += ramp_length
            magnet.length_to_egun = magnet_pos
            magnets_pos[magnet_name] = magnet_pos
        sorted_magnets_pos = sorted(magnets_pos.items(), key=lambda x: x[1])

        for i in range(len(sorted_magnets_pos)):
            magnet_name, magnet_pos = sorted_magnets_pos[i]
            magnet = self._pulsed_magnets[magnet_name]
            magnet.length_to_prev_pulsed_magnet = magnet_pos - prev_magnet_pos
            nominal_delays[magnet_name] = magnet.delay
            prev_magnet_pos = magnet_pos

        length = pyaccel.lattice.length(self._accelerator[:self._extraction_point])
        total_length = prev_total_length + ramp_length + length

        _dict = { 'pulsed_magnet_parameters' : {
            'total_length'     : total_length,
            'magnet_pos'       : magnet_pos,
            'nominal_delays'   : nominal_delays,}
        }
        self._send_parameters_to_other_area_structure(prefix = self._downstream_accelerator_prefix,
                                                      _dict  = _dict)

    def _update_pulsed_magnets_delays(self, delays):
        for magnet_name, delay in delays.items():
            if magnet_name in self._pulsed_magnets.keys():
                self._pulsed_magnets[magnet_name].delay = delay
        self._update_delay_pvs_in_epics_memory()
        self._send_parameters_to_other_area_structure(
            prefix = self._downstream_accelerator_prefix,
            _dict  = {'update_delays' : delays})

    def _update_delay_pvs_in_epics_memory(self):
        for magnet_name, magnet in self._pulsed_magnets.items():
            pv_name = self._magnet2delay[magnet_name]
            value = magnet.delay
            self._others_queue['driver'].put(('s', (pv_name, value)))

    def _get_tune_component(self, plane):
        charge = self._beam_charge.total_value
        if charge == 0.0 or self._tunes == None: return _undef_value
        real_tune = self._tunes[plane].real
        return real_tune

    def _get_equilibrium_at_maximum_energy(self):
        eq = dict()
        # Fix this function!!!
        eq['emittance']       = self._lifetime.emit0
        eq['energy_spread']   = self._lifetime.espread0
        eq['global_coupling'] = self._global_coupling
        return eq

    def _calc_injection_efficiency(self):
        if self.simulate_only_orbit:
            return
        if self._injection_parameters is None:
            return

        if not hasattr(self, '_pulsed_power_supplies'):
            self._injection_efficiency = None
            self._update_injection_efficiency = True
            self._log('calc', '{}: injection efficiency'.format(self.model_module.lattice_version))
            return

        # turn on injection pulsed magnet
        # for psname, ps in self._pulsed_power_supplies.items():
        #     if 'InjKckr' in psname and ps.enabled:
        #         ps.pwrstate_sel = 1

        # calc tracking efficiency
        _dict = self._injection_parameters
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())
        tracking_loss_fraction = injection.calc_charge_loss_fraction_in_ring(self, **_dict)
        self._injection_efficiency = 1.0 - tracking_loss_fraction
        self._log('calc', '{}: injection efficiency {:.2f} %'.format(
            self.model_module.lattice_version, 100*self._injection_efficiency))

        # turn off injection pulsed magnet
        # for psname, ps in self._pulsed_power_supplies.items():
        #     if 'InjKckr' in psname:
        #         ps.pwrstate_sel = 0

    def _calc_ejection_efficiency(self):
        if self.simulate_only_orbit:
            return
        self._log('calc', '{}: ejection efficiency'.format(self.model_module.lattice_version))

        if not hasattr(self, '_pulsed_power_supplies'):
            self._ejection_efficiency = None
            self._update_ejection_efficiency = True
            return

        if self._twiss is None:
            self._ejection_efficiency = 0.0
            return

        # Change energy
        self._accelerator.energy = 3e9 # FIX!!
        self.model_module.lattice.set_rf_voltage(self._accelerator, self._accelerator.energy)

        _dict = {}

        # turn on extraction pulsed magnet
        indices = []
        for psname, ps in self._pulsed_power_supplies.items():
            if 'EjeKckr' in psname: # FIX!!
                # ps.pwrstate_sel = 1
                indices.append(ps.magnet_idx)
        idx = min(indices)
        _dict['accelerator'] = self._accelerator[idx:self._extraction_point+1]

        # calc tracking efficiency
        ejection_parameters = self._get_equilibrium_at_maximum_energy()
        _dict.update(ejection_parameters)
        _dict.update(self._get_vacuum_chamber(init_idx=idx, final_idx=self._extraction_point+1))
        tracking_loss_fraction, twiss, *_ = \
            injection.calc_charge_loss_fraction_in_line(self, init_twiss=self._twiss[idx], **_dict)
        self._ejection_efficiency = 1.0 - tracking_loss_fraction

        # turn off injection pulsed magnet
        # for psname, ps in self._pulsed_power_supplies.items():
        #     if 'EjeK' in psname:
        #         ps.pwrstate_sel = 0

        # Change energy
        self._accelerator.energy = 0.15e9 # FIX!!
        self.model_module.lattice.set_rf_voltage(self._accelerator, self._accelerator.energy)

        # send extraction parameters to downstream accelerator
        args_dict = {}
        args_dict.update(ejection_parameters)
        if twiss is not None:
            args_dict['init_twiss'] = twiss[-1].make_dict()
            self._send_parameters_to_other_area_structure(
                prefix = self._downstream_accelerator_prefix,
                _dict  = {'injection_parameters' : args_dict})

    def _change_injection_bunch(self, charge, charge_time, master_delay, bunch_separation):
        harmonic_number = self._accelerator.harmonic_number
        new_charge = numpy.zeros(harmonic_number)
        new_charge_time = numpy.zeros(harmonic_number)

        for magnet_name, magnet in self._pulsed_magnets.items():
            if 'InjKckr' in magnet_name:
                flight_time = magnet.partial_flight_time
                delay = magnet.delay
                rise_time = magnet.rise_time

        for i in range(len(charge)):
            idx = int(round(round((charge_time[i] - (delay - flight_time + rise_time))/bunch_separation) % harmonic_number))
            new_charge[idx] = charge[i]
            new_charge_time[idx] = charge_time[i]

        return new_charge, new_charge_time

    def _injection_cycle(self, **kwargs):
        charge = kwargs['charge']
        charge_time = kwargs['charge_time']

        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        if self._lifetime is None and not self.simulate_only_orbit:
            self._log(message1='cycle', message2='beam injection in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 0))
            self._log(message1='cycle', message2='beam ejection from {0:s}: {1:.2f}% efficiency'.format(self.prefix, 0))
            return

        charge, charge_time = self._change_injection_bunch(charge, charge_time, kwargs['master_delay'], kwargs['bunch_separation'])

        if CALC_TIMING_EFF and not self.simulate_only_orbit:
            prev_charge = sum(charge)
            for magnet in self._get_sorted_pulsed_magnets():
                charge, charge_time = magnet.pulsed_magnet_pass(charge, charge_time, kwargs['master_delay'])
            efficiency = 100*( sum(charge)/prev_charge) if prev_charge != 0 else 0
            self._log(message1='cycle', message2='pulsed magnet in {0:s}: {1:.4f}% efficiency'.format(self.prefix, efficiency))

        if CALC_INJECTION_EFF and not self.simulate_only_orbit:
            # Injection
            efficiency = self._injection_efficiency if self._injection_efficiency is not None else 0
            charge = [bunch_charge * efficiency for bunch_charge in charge]
            self._beam_inject(charge=charge)
            self._log(message1='cycle', message2='beam injection in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*efficiency))

            # Acceleration
            if self._rampps_enabled:
                self._log(message1='cycle', message2='beam acceleration in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100))
            else:
                self._beam_charge.dump()
                self._log(message1='cycle', message2='beam acceleration in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 0))

            # Extraction
            charge = self._beam_eject()

        kwargs['charge'] = charge
        kwargs['charge_time'] = charge_time
        kwargs['ejection_efficiency'] = self._ejection_efficiency if self._ejection_efficiency is not None else 0
        self._send_parameters_to_other_area_structure(
            prefix = self._downstream_accelerator_prefix,
            _dict  = {'injection_cycle' : kwargs})


class StorageRingModel(RingModel):

    # --- methods implementing response of model to get requests

    def _get_pv_static(self, pv_name, parts):
        if parts.dis == 'DI' and parts.dev == 'BPM':
            charge = self._beam_charge.total_value
            idx = self._get_elements_indices(pv_name)
            if parts.propty == 'PosX-Mon':
                if self._orbit is None or charge == 0.0: return _undef_value
                return _meter_2_nm*self._orbit[0,idx]
            elif parts.propty == 'PosY-Mon':
                if self._orbit is None or charge == 0.0: return _undef_value
                return _meter_2_nm*self._orbit[2,idx]
            return None
        else:
            return super()._get_pv_static(pv_name, parts)

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._state_deprecated:
            self._calc_closed_orbit()
            if not self.simulate_only_orbit:
                self._calc_linear_optics()
                self._calc_equilibrium_parameters()
                self._calc_lifetimes()
            self._update_injection_efficiency = True
            self._state_deprecated = False
            self._state_changed = True
        self._calc_efficiencies()

    def _calc_efficiencies(self):
        # Calculate nlk and on-axis injection efficiencies
        if self._update_injection_efficiency:# and (self._received_charge or self._injection_efficiency is None):
            self._update_injection_efficiency = False
            if not self.simulate_only_orbit:
                self._calc_injection_efficiency()

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)

        # Shift accelerator to start in the injection point
        self._accelerator  = self.model_module.create_accelerator()
        if not hasattr(self, '_injection_point_label'):
            self._others_queue['driver'].put(('a', 'injection point label for ' + self.model_module.lattice_version + ' not defined!'))
        else:
            injection_point    = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', self._injection_point_label)[0]
            if not injection_point:
                self._others_queue['driver'].put(('a', 'injection point label "' + self._injection_point_label + '" not found in ' + self.model_module.lattice_version))
            else:
                self._accelerator  = pyaccel.lattice.shift(self._accelerator, start=injection_point)

        # Append marker to accelerator
        self._append_marker()

        # Create record names dictionary
        self._all_pvs = self.device_names.get_device_names(self._accelerator)
        #self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))

        # Set radiation and cavity on
        if TRACK6D:
            pyaccel.tracking.set6dtracking(self._accelerator)

        self._set_vacuum_chamber()
        self._state_deprecated = True
        self._update_state()

    # --- auxiliary methods

    def _set_pulsed_magnets_parameters(self, **kwargs):
        if 'total_length' in kwargs:
            prev_total_length = kwargs['total_length']
        if 'magnet_pos' in kwargs:
            prev_magnet_pos = kwargs['magnet_pos']
        if 'nominal_delays' in kwargs:
            nominal_delays = kwargs['nominal_delays']

        # for ps in self._pulsed_power_supplies.values():
        #     ps.pwrstate_sel = 0

        magnets_pos = dict()
        for magnet_name, magnet in self._pulsed_magnets.items():
            magnet_pos = prev_total_length + magnet.length_to_inj_point
            magnet.length_to_egun = magnet_pos
            magnets_pos[magnet_name] = magnet_pos
            if 'InjNLKckr' in magnet_name:
                magnet.enabled = 0
        sorted_magnets_pos = sorted(magnets_pos.items(), key=lambda x: x[1])

        for i in range(len(sorted_magnets_pos)):
            magnet_name, magnet_pos = sorted_magnets_pos[i]
            magnet = self._pulsed_magnets[magnet_name]
            magnet.length_to_prev_pulsed_magnet = magnet_pos - prev_magnet_pos
            nominal_delays[magnet_name] = magnet.delay

        delay_values = nominal_delays.values()
        min_delay = min(delay_values)
        for magnet_name in nominal_delays.keys():
            nominal_delays[magnet_name] -= min_delay

        self._others_queue['LI'].put(('p', {'update_delays' : nominal_delays}))

    def _update_pulsed_magnets_delays(self, delays):
        for magnet_name, delay in delays.items():
            if magnet_name in self._pulsed_magnets.keys():
                self._pulsed_magnets[magnet_name].delay = delay
        self._update_delay_pvs_in_epics_memory()

    def _update_delay_pvs_in_epics_memory(self):
        for magnet_name, magnet in self._pulsed_magnets.items():
            pv_name = self._magnet2delay[magnet_name]
            value = magnet.delay
            self._others_queue['driver'].put(('s', (pv_name, value)))

    def _get_tune_component(self, plane):
        charge = self._beam_charge.total_value
        if charge == 0.0 or self._tunes == None: return _undef_value
        real_tune = self._tunes[plane].real
        return real_tune

    def _calc_injection_efficiency(self):
        if self._injection_parameters is None:
            return

        _dict = self._injection_parameters
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())

        for psname, ps in self._pulsed_power_supplies.items():
            if 'InjNLKckr' in psname:
                nlk_enabled = True if ps.enabled else False
            if 'InjDpKckr' in psname:
                kickinj_enabled = True if ps.enabled else False

        if nlk_enabled and not kickinj_enabled:
            # NLK injection efficiency
            self._log('calc', '{}: nlk injection efficiency'.format(self.model_module.lattice_version))
            
            # for psname, ps in self._pulsed_power_supplies.items():
            #     if 'InjNLKckr' in psname and ps.enabled:
            #         ps.pwrstate_sel = 1

            injection_loss_fraction = injection.calc_charge_loss_fraction_in_ring(self, **_dict)
            self._injection_efficiency = 1.0 - injection_loss_fraction
            
            # for psname, ps in self._pulsed_power_supplies.items():
            #     if 'InjNLKckr' in psname:
            #         ps.pwrstate_sel = 0

        elif kickinj_enabled and not nlk_enabled:
            # On-axis injection efficiency
            self._log('calc', '{}: on axis injection efficiency'.format(self.model_module.lattice_version))
            
            # for psname, ps in self._pulsed_power_supplies.items():
            #     if 'InjDpKckr' in psname and ps.enabled:
            #         ps.pwrstate_sel = 1
            
            injection_loss_fraction = injection.calc_charge_loss_fraction_in_ring(self, **_dict)
            self._injection_efficiency = 1.0 - injection_loss_fraction
            
            # for psname, ps in self._pulsed_power_supplies.items():
            #     if 'InjDpKckr' in psname and ps.enabled:
            #         ps.pwrstate_sel = 0

        else:
            self._injection_efficiency = 0

    def _change_injection_bunch(self, charge, charge_time, master_delay, bunch_separation):
        harmonic_number = self._accelerator.harmonic_number
        new_charge = numpy.zeros(harmonic_number)
        new_charge_time = numpy.zeros(harmonic_number)

        for magnet_name, magnet in self._pulsed_magnets.items():
            if 'InjDpKckr' in magnet_name:
                flight_time = magnet.partial_flight_time
                delay = magnet.delay
                rise_time = magnet.rise_time

        for i in range(len(charge)):
            idx = int(round(round((charge_time[i] - (delay - flight_time + rise_time))/bunch_separation) % harmonic_number))
            new_charge[idx] = charge[i]
            new_charge_time[idx] = charge_time[i]

        return new_charge, new_charge_time

    def _injection_cycle(self, **kwargs):
        charge = kwargs['charge']
        charge_time = kwargs['charge_time']

        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        charge, charge_time = self._change_injection_bunch(charge, charge_time, kwargs['master_delay'], kwargs['bunch_separation'])

        if CALC_TIMING_EFF and not self.simulate_only_orbit:
            prev_charge = sum(charge)
            for magnet in self._get_sorted_pulsed_magnets():
                if magnet.enabled:
                    charge, charge_time = magnet.pulsed_magnet_pass(charge, charge_time, kwargs['master_delay'])
            efficiency = 100*( sum(charge)/prev_charge) if prev_charge != 0 else 0
            self._log(message1='cycle', message2='pulsed magnets in {0:s}: {1:.4f}% efficiency'.format(self.prefix, efficiency))

        if CALC_INJECTION_EFF and not self.simulate_only_orbit:
            # Injection
            efficiency = self._injection_efficiency if self._injection_efficiency is not None else 0
            charge = [bunch_charge * efficiency for bunch_charge in charge]
            self._log(message1='cycle', message2='beam injection in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*efficiency))

        self._beam_inject(charge=charge)
