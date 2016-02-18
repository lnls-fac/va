
import math
import numpy
import pyaccel
import mathphys
from . import accelerator_model
from . import beam_charge
from . import injection


_u = accelerator_model._u
UNDEF_VALUE = accelerator_model.UNDEF_VALUE
TRACK6D = accelerator_model.TRACK6D
Plane = accelerator_model.Plane
calc_injection_eff = accelerator_model.calc_injection_eff
calc_timing_eff = accelerator_model.calc_timing_eff


class RingModel(accelerator_model.AcceleratorModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # --- methods implementing response of model to get requests

    def _get_pv_dynamic(self, pv_name):
        if 'DI-CURRENT' in pv_name:
            time_interval = pyaccel.optics.get_revolution_period(self._accelerator)
            currents = self._beam_charge.current(time_interval)
            currents_mA = [bunch_current / _u.mA for bunch_current in currents]
            return sum(currents_mA)
        elif 'DI-BCURRENT' in pv_name:
            time_interval = pyaccel.optics.get_revolution_period(self._accelerator)
            currents = self._beam_charge.current(time_interval)
            currents_mA = [bunch_current / _u.mA for bunch_current in currents]
            return currents_mA
        elif 'PA-LIFETIME' in pv_name:
            return self._beam_charge.total_lifetime / _u.hour
        elif 'PA-BLIFETIME' in pv_name:
            return [lifetime / _u.hour for lifetime in self._beam_charge.lifetime]
        else:
            return None

    def _get_pv_static(self, pv_name):
        value = super()._get_pv_static(pv_name)
        if value is not None:
            return value
        elif '-BPM-' in pv_name:
            charge = self._beam_charge.total_value
            idx = self._get_elements_indices(pv_name)
            if 'FAM:MONIT:X' in pv_name:
                if self._orbit is None or charge == 0.0: return [UNDEF_VALUE]*len(idx)
                return self._orbit[0,idx]
            elif 'FAM:MONIT:Y' in pv_name:
                if self._orbit is None  or charge == 0.0: return [UNDEF_VALUE]*len(idx)
                return self._orbit[2,idx]
            elif 'MONIT:X' in pv_name:
                if self._orbit is None  or charge == 0.0: return [UNDEF_VALUE]
                return self._orbit[0,idx[0]]
            elif 'MONIT:Y' in pv_name:
                if self._orbit is None  or charge == 0.0: return [UNDEF_VALUE]
                return self._orbit[2,idx[0]]
            else:
                return None
        elif 'DI-TUNEH' in pv_name:
            return self._get_tune_component(Plane.horizontal)
        elif 'DI-TUNEV' in pv_name:
            return self._get_tune_component(Plane.vertical)
        elif 'DI-TUNES' in pv_name:
            return self._get_tune_component(Plane.longitudinal)
        elif 'RF-FREQUENCY' in pv_name:
            return pyaccel.optics.get_rf_frequency(self._accelerator)
        elif 'RF-VOLTAGE' in pv_name:
            idx = self._get_elements_indices(pv_name)
            return self._accelerator[idx[0]].voltage
        elif 'PA-CHROMX' in pv_name:
            return UNDEF_VALUE
        elif 'PA-CHROMY' in pv_name:
            return UNDEF_VALUE
        elif 'PA-EMITX' in pv_name:
            return UNDEF_VALUE
        elif 'PA-EMITY' in pv_name:
            return UNDEF_VALUE
        elif 'PA-SIGX' in pv_name:
            return UNDEF_VALUE
        elif 'PA-SIGY' in pv_name:
            return UNDEF_VALUE
        elif 'PA-SIGS' in pv_name:
            return UNDEF_VALUE
        else:
            return None

  # --- methods implementing response of model to set requests

    def _set_pv_rf(self, pv_name, value):
        if 'RF-VOLTAGE' in pv_name:
            idx = self._get_elements_indices(pv_name)
            prev_value = self._accelerator[idx[0]].voltage
            if value != prev_value:
                self._accelerator[idx[0]].voltage = value
                self._state_deprecated = True
            return True
        elif 'RF-FREQUENCY' in pv_name:
            idx = self._get_elements_indices(pv_name)
            prev_value = self._accelerator[idx[0]].frequency
            if value != prev_value:
                self._accelerator[idx[0]].frequency = value
                self._state_deprecated = True
            return True
        return False

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._state_deprecated:
            self._calc_closed_orbit()
            self._calc_linear_optics()
            self._calc_equilibrium_parameters()
            self._calc_lifetimes()
            self._update_injection_efficiency = True
            self._state_deprecated = False
            self._state_changed = True
        self._calc_efficiencies()

    def _calc_efficiencies(self):
        # Calculate pmm and on-axis injection efficiencies
        if self._update_injection_efficiency and (self._received_charge or self._injection_efficiency is None):
            self._update_injection_efficiency = False
            self._calc_injection_efficiency()

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)

        # Shift accelerator to start in the injection point
        self._accelerator  = self.model_module.create_accelerator()
        if not hasattr(self, '_injection_point_label'):
            self._send_queue.put(('a', 'injection point label for ' + self.model_module.lattice_version + ' not defined!'))
        else:
            injection_point    = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', self._injection_point_label)[0]
            if not injection_point:
                self._send_queue.put(('a', 'injection point label "' + self._injection_point_label + '" not found in ' + self.model_module.lattice_version))
            else:
                self._accelerator  = pyaccel.lattice.shift(self._accelerator, start = injection_point)

        # Append marker to accelerator
        self._append_marker()

        # Create record names dictionary
        self._all_pvs = self.model_module.device_names.get_device_names(self._accelerator)
        self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))

        # Set radiation and cavity on
        if TRACK6D:
            pyaccel.tracking.set6dtracking(self._accelerator)

        self._set_vacuum_chamber()
        self._state_deprecated = True
        self._update_state()

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        if self._beam_charge: self._beam_charge.dump()
        self._orbit = None
        self._twiss = None
        self._m66 = None
        self._tunes = None
        self._transfer_matrices = None
        self._summary = None
        self._injection_efficiency = None
        self._received_charge = False

   # --- auxiliary methods

    def _set_pulsed_magnets_parameters(self, **kwargs):
        if 'total_length' in kwargs:
            prev_total_length = kwargs['total_length']
        if 'magnet_pos' in kwargs:
            prev_magnet_pos = kwargs['magnet_pos']
        if 'nominal_delays' in kwargs:
            nominal_delays = kwargs['nominal_delays']

        for ps in self._pulsed_power_supplies.values(): ps.turn_off()

        magnets_pos = dict()
        for magnet_name, magnet in self._pulsed_magnets.items():
            magnet_pos = prev_total_length + magnet.length_to_inj_point
            magnet.length_to_egun = magnet_pos
            magnets_pos[magnet_name] = magnet_pos
            if 'PMM' in magnet_name: magnet.enabled = 0
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

        self._send_queue.put(('p', ('LI', {'update_delays' : nominal_delays})))

    def _update_pulsed_magnets_delays(self, delays):
        for magnet_name, delay in delays.items():
            if magnet_name in self._pulsed_magnets.keys():
                self._pulsed_magnets[magnet_name].delay = delay
        self._update_delay_pvs_in_epics_memory()
        self._send_initialisation_sign()

    def _update_delay_pvs_in_epics_memory(self):
        for magnet_name, magnet in self._pulsed_magnets.items():
            pv_name = self._magnet2delay[magnet_name]
            value = magnet.delay
            self._send_queue.put(('s', (pv_name, value)))

    def _get_tune_component(self, plane):
        charge = self._beam_charge.total_value
        if charge == 0.0 or self._tunes == None: return UNDEF_VALUE
        real_tune = self._tunes[plane].real
        return real_tune

    def _calc_closed_orbit(self):
        # Calculate closed orbit when there is beam
        try:
            self._log('calc', 'closed orbit for '+self.model_module.lattice_version)
            if TRACK6D:
                self._orbit = pyaccel.tracking.findorbit6(self._accelerator, indices='open')
            else:
                self._orbit = numpy.zeros((6,len(self._accelerator)))
                self._orbit[:4,:] = pyaccel.tracking.findorbit4(self._accelerator, indices='open')
        # Beam is lost
        except pyaccel.tracking.TrackingException:
            self._beam_dump('panic', 'BEAM LOST: closed orbit does not exist', c='red')

    def _calc_linear_optics(self):
        # Calculate linear optics when there is beam
        if self._orbit is None: return
        try:
        # Optics
            self._log('calc', 'linear optics for '+self.model_module.lattice_version)
            self._twiss, self._m66 = pyaccel.optics.calc_twiss(self._accelerator, fixed_point=self._orbit[:,0])
            self._tunes = pyaccel.optics.get_frac_tunes(m66=self._m66)
        # Beam is lost
        except numpy.linalg.linalg.LinAlgError:
            self._beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')
        except pyaccel.optics.OpticsException:
            self._beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')
        except pyaccel.tracking.TrackingException:
            self._beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')

    def _calc_equilibrium_parameters(self):
        if self._m66 is None: return
        try:
            self._log('calc', 'equilibrium parameters for '+self.model_module.lattice_version)
            self._summary, *_ = pyaccel.optics.get_equilibrium_parameters(\
                                         accelerator=self._accelerator,
                                         twiss=self._twiss,
                                         m66=self._m66,
                                         closed_orbit=self._orbit)
        except:
            self._beam_dump('panic', 'BEAM LOST: unable to calc equilibrium parameters', c='red')

    def _calc_lifetimes(self):
        if self._summary is None or self._beam_charge is None: return

        self._log('calc', 'beam lifetimes for '+self.model_module.lattice_version)

        Ne1C = 1.0/mathphys.constants.elementary_charge # number of electrons in 1 coulomb
        coupling = self.model_module.accelerator_data['global_coupling']
        pressure_profile = self.model_module.accelerator_data['pressure_profile']

        e_lifetime, i_lifetime, q_lifetime, t_coeff = pyaccel.lifetime.calc_lifetimes(self._accelerator,
                                           Ne1C, coupling, pressure_profile, self._twiss, self._summary)
        self._beam_charge.set_lifetimes(elastic=e_lifetime, inelastic=i_lifetime,
                                        quantum=q_lifetime, touschek_coefficient=t_coeff)

    def _calc_injection_efficiency(self):
        if self._injection_parameters is None: return

        _dict = self._injection_parameters
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())

        for ps_name, ps in self._pulsed_power_supplies.items():
            if 'PMM' in ps_name:
                pmm_enabled = True if ps.enabled else False
            if 'INJ' in ps_name:
                kickinj_enabled = True if ps.enabled else False

        if pmm_enabled and not kickinj_enabled:
            # PMM injection efficiency
            self._log('calc', 'pmm injection efficiency  for ' + self.model_module.lattice_version)
            for ps_name, ps in self._pulsed_power_supplies.items():
                if 'PMM' in ps_name and ps.enabled: ps.turn_on()
            injection_loss_fraction = injection.calc_charge_loss_fraction_in_ring(self._accelerator, **_dict)
            self._injection_efficiency = 1.0 - injection_loss_fraction
            for ps_name, ps in self._pulsed_power_supplies.items():
                if 'PMM' in ps_name: ps.turn_off()

        elif kickinj_enabled and not pmm_enabled:
            # On-axis injection efficiency
            self._log('calc', 'on axis injection efficiency  for '+self.model_module.lattice_version)
            for ps_name, ps in self._pulsed_power_supplies.items():
                if 'INJ' in ps_name and ps.enabled: ps.turn_on()
            injection_loss_fraction = injection.calc_charge_loss_fraction_in_ring(self._accelerator, **_dict)
            self._injection_efficiency = 1.0 - injection_loss_fraction
            for ps_name, ps in self._pulsed_power_supplies.items():
                if 'INJ' in ps_name and ps.enabled: ps.turn_off()

        else:
            self._injection_efficiency = 0

    def _change_injection_bunch(self, charge, charge_time, master_delay, bunch_separation):
        harmonic_number = self._accelerator.harmonic_number
        new_charge = numpy.zeros(harmonic_number)
        new_charge_time = numpy.zeros(harmonic_number)

        for magnet_name, magnet in self._pulsed_magnets.items():
            if 'INJ' in magnet_name:
                flight_time = magnet.partial_flight_time
                delay = magnet.delay
                rise_time = magnet.rise_time

        for i in range(len(charge)):
            idx = round(round((charge_time[i] - (delay - flight_time + rise_time))/bunch_separation) % harmonic_number)
            new_charge[idx] = charge[i]
            new_charge_time[idx] = charge_time[i]

        return new_charge, new_charge_time

    def _injection_cycle(self, **kwargs):
        charge = kwargs['charge']
        charge_time = kwargs['charge_time']

        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        charge, charge_time = self._change_injection_bunch(charge, charge_time, kwargs['master_delay'], kwargs['bunch_separation'])

        if calc_timing_eff:
            prev_charge = sum(charge)
            for magnet in self._get_sorted_pulsed_magnets():
                if magnet.enabled:
                    charge, charge_time = magnet.pulsed_magnet_pass(charge, charge_time, kwargs['master_delay'])
            efficiency = 100*( sum(charge)/prev_charge) if prev_charge != 0 else 0
            self._log(message1='cycle', message2='pulsed magnets in {0:s}: {1:.4f}% efficiency'.format(self.prefix, efficiency))

        if calc_injection_eff:
            # Injection
            efficiency = self._injection_efficiency if self._injection_efficiency is not None else 0
            charge = [bunch_charge * efficiency for bunch_charge in charge]
            self._log(message1='cycle', message2='beam injection in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*efficiency))

        self._beam_inject(charge=charge)
