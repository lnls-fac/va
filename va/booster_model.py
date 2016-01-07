
import math
import numpy
import pyaccel
import mathphys
from . import accelerator_model
from . import beam_charge
from . import utils
from . import injection


_u = mathphys.units
UNDEF_VALUE = utils.UNDEF_VALUE
TRACK6D = accelerator_model.TRACK6D
Plane = accelerator_model.Plane


class BoosterModel(accelerator_model.AcceleratorModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # --- methods implementing response of model to get requests

    def _get_pv_fake(self, pv_name):
        return super()._get_pv_fake(pv_name)

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

    def _get_tune_component(self, plane):
        charge = self._beam_charge.total_value
        if charge == 0.0 or self._tunes == None: return UNDEF_VALUE
        real_tune = self._tunes[plane].real
        return real_tune

    def _get_pv_timing(self, pv_name):
        if 'TI-' in pv_name:
            if 'KICKINJ-ENABLED' in pv_name:
                return self._ti_kickinj_enabled
            elif 'KICKINJ-DELAY' in pv_name:
                return self._ti_kickinj_delay
            elif 'KICKEX-ENABLED' in pv_name:
                return self._ti_kickex_enabled
            elif 'KICKEX-DELAY' in pv_name:
                return self._ti_kickex_delay
            elif 'KICKEX-INC' in pv_name:
                return self._ti_kickex_inc
            elif 'RAMPPS-ENABLED' in pv_name:
                return self._ti_rampps_enabled
            elif 'RAMPPS-DELAY' in pv_name:
                return self._ti_rampps_delay
            else:
                return None
        else:
            return None

    # --- methods implementing response of model to set requests

    def _set_pv_fake(self, pv_name, value):
        return super()._set_pv_fake(pv_name, value)

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
            self._send_queue.put(('g', ('LI', 'SIRF-FREQUENCY')))
            return True
        return False

    def _set_pv_timing(self, pv_name, value):
        if 'TI-' in pv_name:
            if 'KICKINJ-ENABLED' in pv_name:
                self._ti_kickinj_enabled = value
                self._state_deprecated = True
                return True
            elif 'KICKINJ-DELAY' in pv_name:
                self._ti_kickinj_delay = value
                self._state_deprecated = True
                return True
            elif 'KICKEX-ENABLED' in pv_name:
                self._ti_kickex_enabled = value
                self._state_deprecated = True
                return True
            elif 'KICKEX-DELAY' in pv_name:
                self._ti_kickex_delay = value
                self._state_deprecated = True
                return True
            elif 'KICKEX-INC' in pv_name:
                self._ti_kickex_inc = value
                self._state_deprecated = True
                return True
            elif 'RAMPPS-ENABLED' in pv_name:
                self._ti_rampps_enabled = value
                self._state_deprecated = True
                return True
            elif 'RAMPPS-DELAY' in pv_name:
                self._ti_rampps_delay = value
                self._state_deprecated = True
                return True
            else:
                return False
        else:
            return False

    # --- methods that help updating the model state

    def _update_state(self, force=False):

        if force or self._state_deprecated:
            # Calculate parameters
            self._calc_closed_orbit()
            self._calc_linear_optics()
            self._calc_equilibrium_parameters()
            self._calc_lifetimes()
            self._update_injection_efficiency = True
            self._update_ejection_efficiency  = True
            self._state_changed = True
            self._state_deprecated = False
        # Calculate injection and ejection efficiencies
        self._calc_efficiencies()

    def _calc_efficiencies(self):
        if self._summary is None:
            self._update_injection_efficiency = False
            self._update_ejection_efficiency  = False
            return

        # Calculate injection efficiency
        if self._update_injection_efficiency and (self._received_charge or self._injection_efficiency is None):
            self._update_injection_efficiency = False
            self._calc_injection_efficiency()

        # Calculate ejection efficiency
        if self._update_ejection_efficiency  and (self._received_charge or self._ejection_efficiency is None):
            self._update_ejection_efficiency = False
            self._calc_ejection_efficiency()

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)

        # Shift accelerator to start in the injection point
        self._accelerator  = self.model_module.create_accelerator()
        #injection_point    = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'sept_in')[0]
        print(self._injection_point_label)
        print(self._downstream_accelerator_prefix)

        if self._injection_point_label is None:
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

        if TRACK6D:
            # Set radiation and cavity on
            pyaccel.tracking.set6dtracking(self._accelerator)

        self._ext_point    = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'sept_ex')[0]
        self._kickin_idx   = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'kick_in')
        self._kickex_idx   = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'kick_ex')
        self._set_vacuum_chamber()

        self._state_deprecated = True
        self._update_state()

        # Initial values of timing pvs
        self._ti_kickinj_enabled = 1
        self._ti_kickinj_delay = 0
        self._ti_kickex_enabled = 1
        self._ti_kickex_delay = 0
        self._ti_kickex_inc = 0
        self._ti_rampps_enabled = 1
        self._ti_rampps_delay = 0

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
        self._received_charge = False
        self._injection_efficiency = None
        self._ejection_efficiency  = None

   # --- auxiliary methods

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


    def _get_equilibrium_at_maximum_energy(self):
        eq = dict()
        eq['emittance']       = self._summary['natural_emittance']
        eq['energy_spread']   = self._summary['natural_energy_spread']
        eq['global_coupling'] = self.model_module.accelerator_data['global_coupling']
        return eq

    def _set_kickin(self, str ='off'):
        for idx in self._kickin_idx:
            if str.lower() == 'on':
                self._accelerator[idx].hkick_polynom = self._kickin_angle
            elif str.lower() == 'off':
                self._accelerator[idx].hkick_polynom = 0.0

    def _set_kickex(self, str ='off'):
        for idx in self._kickex_idx:
            if str.lower() == 'on':
                self._accelerator[idx].hkick_polynom = self._kickex_angle
            elif str.lower() == 'off':
                self._accelerator[idx].hkick_polynom = 0.0

    def _calc_injection_efficiency(self):
        if self._injection_parameters is None: return
        self._log('calc', 'injection efficiency  for '+self.model_module.lattice_version)

        _dict = self._injection_parameters
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())

        self._set_kickin('on')
        injection_loss_fraction = injection.calc_charge_loss_fraction_in_ring(self._accelerator, **_dict)
        self._injection_efficiency = 1.0 - injection_loss_fraction
        self._set_kickin('off')

    def _calc_ejection_efficiency(self):
        if self._twiss is None:
            self._ejection_efficiency = 0.0
            return

        self._log('calc', 'ejection efficiency  for '+self.model_module.lattice_version)
        self._set_kickex('on')
        accelerator = self._accelerator[self._kickex_idx[0]:self._ext_point+1]

        ejection_parameters = self._get_equilibrium_at_maximum_energy()
        _dict = {}
        _dict.update(ejection_parameters)
        _dict.update(self._get_vacuum_chamber(init_idx=self._kickex_idx[0], final_idx=self._ext_point+1))

        ejection_loss_fraction, twiss, *_ = injection.calc_charge_loss_fraction_in_line(accelerator,
            init_twiss=self._twiss[self._kickex_idx[0]], **_dict)
        self._ejection_efficiency = 1.0 - ejection_loss_fraction

        args_dict = {}
        args_dict.update(ejection_parameters)
        args_dict['init_twiss'] = twiss[-1].make_dict() # picklable object
        self._send_parameters_to_downstream_accelerator(args_dict)
        self._set_kickex('off')

    def _injection(self, charge=None, delay=0.0, li_charge=None):
        if charge is None: return

        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        if self._summary is None:
            self._log(message1='cycle', message2='beam injection in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 0))
            self._log(message1='cycle', message2='beam ejection from {0:s}: {1:.2f}% efficiency'.format(self.prefix, 0))
            return

        if not self._ti_kickinj_enabled: self._injection_efficiency = 0.0
        self._beam_inject(charge=charge)
        self._log(message1='cycle', message2='beam injection in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*self._injection_efficiency))

        if not self._ti_kickex_enabled: self._ejection_efficiency = 0.0
        final_charge = self._beam_eject()
        self._log(message1='cycle', message2='beam ejection from {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*self._ejection_efficiency))

        delay += self._ti_kickex_delay
        self._send_charge_to_downstream_accelerator({'charge' : final_charge, 'delay' : delay, 'li_charge': li_charge})
