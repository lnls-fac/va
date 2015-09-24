
import math
import numpy
import pyaccel
import mathphys
from . import accelerator_model
from . import beam_charge
from . import utils
from . import injection


UNDEF_VALUE = utils.UNDEF_VALUE
TRACK6D = True
indices = 'closed'
_u = mathphys.units


class RingModel(accelerator_model.AcceleratorModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Send value of SIRF-FREQUENCY to LI
        self._send_queue.put(('g', ('LI', 'SIRF-FREQUENCY')))

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
        elif 'DI-TUNEH' in pv_name:
            charge = self._beam_charge.total_value
            if self._twiss is None or charge == 0.0: return UNDEF_VALUE
            print('mux ',self._twiss[-1].mux)
            tune_value = self._twiss[-1].mux / 2.0 / math.pi
            return tune_value
        elif 'DI-TUNEV' in pv_name:
            charge = self._beam_charge.total_value
            if self._twiss is None or charge == 0.0: return UNDEF_VALUE
            tune_value = self._twiss[-1].muy / 2.0 / math.pi
            return tune_value
        elif 'DI-TUNES' in pv_name:
            return UNDEF_VALUE
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
                return self._ti_kickinj_enabled
            elif 'KICKINJ-DELAY' in pv_name:
                return self._ti_kickinj_delay
            elif 'PMM-ENABLED' in pv_name:
                return self._ti_pmm_enabled
            elif 'PMM-DELAY' in pv_name:
                return self._ti_pmm_delay
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
            elif 'PMM-ENABLED' in pv_name:
                self._ti_pmm_enabled = value
                self._state_deprecated = True
                return True
            elif 'PMM-DELAY' in pv_name:
                self._ti_pmm_delay = value
                self._state_deprecated = True
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
            self._calc_injection_efficiency = True
            self._state_deprecated = False
            self._state_changed = True

        # Calculate injection efficiency
        if self._calc_injection_efficiency and (self._received_charge or
                self._onaxis_injection_loss_fraction is None or self._pmm_injection_loss_fraction is None):
            self._calc_injection_efficiency = False
            self._set_kickin('on')
            self._calc_onaxis_injection_loss_fraction()
            self._set_kickin('off')
            self._set_pmm('on')
            self._calc_pmm_injection_loss_fraction()
            self._set_pmm('off')


    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)

        # Shift accelerator and record names to start in the injection point
        accelerator        = self.model_module.create_accelerator()
        injection_point    = pyaccel.lattice.find_indices(accelerator, 'fam_name', 'sept_in')[0]
        self._accelerator  = pyaccel.lattice.shift(accelerator, start = injection_point)
        self._all_pvs      = utils.shift_record_names(self._accelerator, self._all_pvs)

        if TRACK6D:
            pyaccel.tracking.set6dtracking(self._accelerator)

        self._kickin_idx   = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'kick_in')
        self._pmm_idx   = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'pmm')
        self._set_vacuum_chamber(indices=indices)

        # Initial values of timing pvs
        self._ti_kickinj_enabled = 1
        self._ti_kickinj_delay = 0
        self._ti_pmm_enabled = 0
        self._ti_pmm_delay = 0
        self._ti_egun_delay = 0
        self._ti_kickex_inc = 0
        self._state_deprecated = True
        self._update_state()

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        if self._beam_charge: self._beam_charge.dump()
        self._orbit = None
        self._twiss = None
        self._m66 = None
        self._transfer_matrices = None
        self._summary = None
        # self._injection_parameters = None
        self._injection_loss_fraction = None
        self._pmm_injection_loss_fraction = None
        self._onaxis_injection_loss_fraction = None
        self._received_charge = False

   # --- auxilliary methods

    def _calc_closed_orbit(self):
        # Calculate closed orbit when there is beam
        try:
            self._log('calc', 'closed orbit for '+self.model_module.lattice_version)
            if TRACK6D:
                self._orbit = pyaccel.tracking.findorbit6(self._accelerator, indices=indices)
            else:
                n = len(self._accelerator)+1 if indices == 'closed' else len(self._accelerator)
                self._orbit = numpy.zeros((6,n))
                self._orbit[:4,:] = pyaccel.tracking.findorbit4(self._accelerator, indices=indices)
        # Beam is lost
        except pyaccel.tracking.TrackingException:
            self._beam_dump('panic', 'BEAM LOST: closed orbit does not exist', c='red')

    def _calc_linear_optics(self):
        # Calculate linear optics when there is beam
        if self._orbit is None: return
        try:
        # Optics
            self._log('calc', 'linear optics for '+self.model_module.lattice_version)
            self._twiss, self._m66, self._transfer_matrices, self._orbit = \
                pyaccel.optics.calc_twiss(self._accelerator, fixed_point=self._orbit[:,0], indices=indices)
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
                                         transfer_matrices=self._transfer_matrices,
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

    def _set_kickin(self, str ='off'):
        for idx in self._kickin_idx:
            if str.lower() == 'on':
                self._accelerator[idx].hkick_polynom = self._kickin_angle
            elif str.lower() == 'off':
                self._accelerator[idx].hkick_polynom = 0.0

    def _set_pmm(self, str ='off'):
        for idx in self._pmm_idx:
            if str.lower() == 'on':
                self._accelerator[idx].polynom_b = numpy.array(self._pmm_integ_polynom_b)/self._accelerator[idx].length
            elif str.lower() == 'off':
                self._accelerator[idx].polynom_b = [0.0]*len(self._accelerator[idx].polynom_b)

    def _calc_pmm_injection_loss_fraction(self):
        if self._injection_parameters is None: return
        self._log('calc', 'pmm injection efficiency  for '+self.model_module.lattice_version)

        _dict = self._injection_parameters
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())
        self._pmm_injection_loss_fraction = injection.calc_charge_loss_fraction_in_ring(self._accelerator, **_dict)

    def _calc_onaxis_injection_loss_fraction(self):
        if self._injection_parameters is None: return
        self._log('calc', 'on axis injection efficiency  for '+self.model_module.lattice_version)

        _dict = self._injection_parameters
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())
        self._onaxis_injection_loss_fraction = injection.calc_charge_loss_fraction_in_ring(self._accelerator, **_dict)

    def _injection(self, charge=None):
        if charge is None: return

        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        charge = self._incoming_bunch_injected_in_si(charge)
        if self._ti_kickinj_enabled and not self._ti_pmm_enabled:
            self._injection_loss_fraction = self._onaxis_injection_loss_fraction
            efficiency = self._beam_inject(charge=charge)
        elif self._ti_kickinj_enabled and not self._ti_pmm_enabled:
            self._injection_loss_fraction = self._pmm_injection_loss_fraction
            efficiency = self._beam_inject(charge=charge)
        else:
            charge = 0.0
            efficiency = 0
        self._log(message1='cycle', message2='beam injection in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*efficiency))

    def _receive_pv_value(self, pv_name, value):
        if 'TI-EGUN-DELAY' in pv_name:
            self._prev_ti_egun_delay = self._ti_egun_delay
            self._ti_egun_delay = value
        elif 'TI-KICKEX-INC' in pv_name:
            self._prev_ti_kickex_inc = self._ti_kickex_inc
            self._ti_kickex_inc = value

    def _incoming_bunch_injected_in_si(self, charge):
        # Change the bunches in which the charge is injected
        rf_frequency = pyaccel.optics.get_rf_frequency(self._accelerator)
        bunch_offset = round((self._prev_ti_egun_delay + self._prev_ti_kickex_inc) * rf_frequency)
        harmonic_number = self.model_module.harmonic_number
        bunch_charge = [0.0] * harmonic_number
        for i in range(len(charge)):
            n = (i + bunch_offset) % harmonic_number
            bunch_charge[n] += charge[i]
        return bunch_charge
