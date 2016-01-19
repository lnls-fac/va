
import math
import numpy
import pyaccel
import mathphys
from . import accelerator_model
from . import beam_charge
from . import utils
from . import injection


_c = accelerator_model._c
_u = accelerator_model._u
UNDEF_VALUE = accelerator_model.UNDEF_VALUE
TRACK6D = accelerator_model.TRACK6D
Plane = accelerator_model.Plane


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
            if 'FAM-X' in pv_name:
                if self._orbit is None or charge == 0.0: return [UNDEF_VALUE]*len(idx)
                return self._orbit[0,idx]
            elif 'FAM-Y' in pv_name:
                if self._orbit is None  or charge == 0.0: return [UNDEF_VALUE]*len(idx)
                return self._orbit[2,idx]
            else:
                if self._orbit is None  or charge == 0.0: return [UNDEF_VALUE]*2
                return self._orbit[[0,2],idx[0]]
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

    def _get_pv_timing(self, pv_name):
        if 'TI-' in pv_name:
            if 'KICKINJ-ENABLED' in pv_name:
                return self._injection_kick_enabled
            elif 'PMM-ENABLED' in pv_name:
                return self._pmm_enabled
            elif 'KICKINJ-DELAY' in pv_name:
                if not hasattr(self, '_injection_kick_delay'):
                    return UNDEF_VALUE
                return self._injection_kick_delay
            elif 'PMM-DELAY' in pv_name:
                if not hasattr(self, '_pmm_delay'):
                    return UNDEF_VALUE
                return self._pmm_delay
            else:
                return None
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

    def _set_pv_timing(self, pv_name, value):
        if 'TI-' in pv_name:
            if 'KICKINJ-ENABLED' in pv_name:
                self._injection_kick_enabled = value
                return True
            elif 'PMM-ENABLED' in pv_name:
                self._pmm_enabled = value
                return True
            elif 'KICKINJ-DELAY' in pv_name:
                self._injection_kick_delay = value
                return True
            elif 'PMM-DELAY' in pv_name:
                self._pmm_delay = value
                return True
            else:
                return False
        else:
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

        # Calculate pmm and on-axis injection efficiencies
        if self._update_injection_efficiency and (self._received_charge or
            self._onaxis_injection_efficiency is None or self._pmm_injection_efficiency is None):
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
        self._all_pvs = self.model_module.record_names.get_record_names(self._accelerator)
        self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))

        # Set radiation and cavity on
        if TRACK6D:
            pyaccel.tracking.set6dtracking(self._accelerator)

        self._injection_kick_idx = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', self._injection_kick_label)
        self._pmm_idx = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', self._pmm_label)
        self._set_vacuum_chamber()
        self._injection_kick_enabled = 1
        self._pmm_enabled = 0
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
        self._injection_efficiency        = None
        self._total_efficiency            = None
        self._pmm_injection_efficiency    = None
        self._onaxis_injection_efficiency = None
        self._received_charge = False

   # --- auxiliary methods

    def _calc_nominal_delays(self, path_length=None, bunch_separation=None, nr_bunches=None, egun_delay=None):
        self._bunch_separation = bunch_separation
        half_pulse_duration = nr_bunches * self._bunch_separation/2.0

        # Calculate injection kick nominal delay
        injpoint_to_kick_len = pyaccel.lattice.length(self._accelerator[:self._injection_kick_idx[0]])
        self._injection_kick_nominal_delay = (path_length + injpoint_to_kick_len)/_c - self._injection_kick_rise_time + half_pulse_duration
        self._injection_kick_delay = self._injection_kick_nominal_delay

        # Calculate pmm nominal delay
        injpoint_to_pmm_len = pyaccel.lattice.length(self._accelerator[:self._pmm_idx[0]])
        self._pmm_nominal_delay = (path_length + injpoint_to_pmm_len)/_c - self._pmm_rise_time + half_pulse_duration
        self._pmm_delay = self._pmm_nominal_delay

        # Update epics memory
        self._update_delay_pvs_in_epics_memory()
        self._send_initialisation_sign()

    def _update_delay_pvs_in_epics_memory(self):
        self._send_queue.put(('s', ('SITI-KICKINJ-DELAY', self._injection_kick_nominal_delay)))
        self._send_queue.put(('s', ('SITI-PMM-DELAY', self._pmm_nominal_delay)))

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

    def _beam_inject(self, charge=None, bunch_idx=0):
        if charge is None: return

        initial_charge = self._beam_charge.total_value
        self._beam_charge.inject(charge, bunch_idx=bunch_idx)

        final_charge = self._beam_charge.total_value
        if (initial_charge == 0) and (final_charge != initial_charge):
            self._state_changed = True

    def _calc_injection_efficiency(self):
        if self._injection_parameters is None: return

        _dict = self._injection_parameters
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())

        # PMM injection efficiency
        self._log('calc', 'pmm injection efficiency  for '+self.model_module.lattice_version)
        for idx in self._pmm_idx:
            self._accelerator[idx].polynom_b = numpy.array(self._pmm_integ_polynom_b)/self._accelerator[idx].length
        injection_loss_fraction = injection.calc_charge_loss_fraction_in_ring(self._accelerator, **_dict)
        self._pmm_injection_efficiency = 1.0 - injection_loss_fraction
        for idx in self._pmm_idx:
            self._accelerator[idx].polynom_b = [0.0]*len(self._accelerator[idx].polynom_b)

        # On-axis injection efficiency
        self._log('calc', 'on axis injection efficiency  for '+self.model_module.lattice_version)
        for idx in self._injection_kick_idx:
            self._accelerator[idx].hkick_polynom = self._injection_kick_angle
        injection_loss_fraction = injection.calc_charge_loss_fraction_in_ring(self._accelerator, **_dict)
        self._onaxis_injection_efficiency = 1.0 - injection_loss_fraction
        for idx in self._injection_kick_idx:
            self._accelerator[idx].hkick_polynom = 0.0

    def _calc_injection_magnet_efficiency(self, nr_bunches):
        if self._injection_kick_enabled and not self._pmm_enabled:
            rise_time     = self._injection_kick_rise_time
            delay         = self._injection_kick_delay
            nominal_delay = self._injection_kick_nominal_delay
            injection_magnet_efficiency = injection.calc_pulsed_magnet_efficiency(rise_time, delay, nominal_delay, self._bunch_separation, nr_bunches)
            self._injection_efficiency = self._onaxis_injection_efficiency
        elif not self._injection_kick_enabled and self._pmm_enabled:
            rise_time     = self._pmm_rise_time
            delay         = self._pmm_delay
            nominal_delay = self._pmm_nominal_delay
            injection_magnet_efficiency = injection.calc_pulsed_magnet_efficiency(rise_time, delay, nominal_delay, self._bunch_separation, nr_bunches)
            self._injection_efficiency = self._pmm_injection_efficiency
        else:
            injection_magnet_efficiency = 0
            self._injection_efficiency = 0.0
        return injection_magnet_efficiency

    def _injection_cycle(self, **kwargs):
        charge = kwargs['charge']
        injection_bunch = kwargs['injection_bunch']
        linac_charge = kwargs['linac_charge']

        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        nr_bunches = len(charge)
        initial_charge = charge

        injection_magnet_efficiency = self._calc_injection_magnet_efficiency(nr_bunches)
        charge = injection_magnet_efficiency * charge
        charge = [bunch_charge * self._injection_efficiency for bunch_charge in charge]
        self._beam_inject(charge=charge, bunch_idx=injection_bunch)
        self._log(message1='cycle', message2='beam injection in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*(sum(charge)/sum(initial_charge))))

        self._total_efficiency = self._injection_efficiency*(sum(charge)/sum(linac_charge))
        self._log(message1 = 'cycle', message2 = '--')
        self._log(message1='cycle', message2='total efficiency: {0:.2f}%'.format(100*self._total_efficiency))
