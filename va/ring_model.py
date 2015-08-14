
import time
import math
import numpy
import pyaccel
import mathphys
from . import accelerator_model


TRACK6D = False
UNDEF_VALUE = accelerator_model.UNDEF_VALUE
_u = mathphys.units


class RingModel(accelerator_model.AcceleratorModel):

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
            self._state_deprecated = False
            self._calc_closed_orbit()
            self._calc_linear_optics()
            self._calc_equilibrium_parameters()
            self._calc_lifetimes()
            self._injection_loss_fraction = 0.0
            self._ejection_loss_fraction = 0.0

    def _receive_pv_value(self, pv_name, value):
        if 'SI-KICKIN-ENABLED' in pv_name:
            self._ti_si_kickin_on = value
        elif 'SI-KICKIN-DELAY' in pv_name:
            self._ti_si_kickin_delay = value
        elif 'TI-DELAY' in pv_name:
            self._ti_delay = value

    def _get_charge_from_upstream_accelerator(self, charge=None):
        if charge is None: return
        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))
        charge = self._incoming_bunch_injected_in_si(charge)
        if not self._ti_si_kickin_on:
            charge = [0.0]
        efficiency = self._beam_inject(charge=charge)
        if not self._ti_si_kickin_on:
            efficiency = 0
        self._log(message1='cycle', message2='beam injection in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*efficiency))
        self._pipe.send(('g', ('TI', 'SIRF-FREQUENCY')))

   # --- auxilliary methods

    def _calc_closed_orbit(self):
        # calcs closed orbit when there is beam
        try:
            self._log('calc', 'closed orbit for '+self.model_module.lattice_version)
            if TRACK6D:
                self._orbit = pyaccel.tracking.findorbit6(self._accelerator, indices='open')
            else:
                self._orbit = numpy.zeros((6,len(self._accelerator)))
                self._orbit[:4,:] = pyaccel.tracking.findorbit4(self._accelerator, indices='open')
        # beam is lost
        except pyaccel.tracking.TrackingException:
            self._beam_dump('panic', 'BEAM LOST: closed orbit does not exist', c='red')

    def _calc_linear_optics(self):
        # calcs linear optics when there is beam
        if self._orbit is None: return
        try:
        # optics
            self._log('calc', 'linear optics for '+self.model_module.lattice_version)
            self._twiss, self._m66, self._transfer_matrices, self._orbit = \
                pyaccel.optics.calc_twiss(self._accelerator, fixed_point=self._orbit[:,0])
        # beam is lost
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

        e_lifetime, i_lifetime, q_lifetime, t_coeff = pyaccel.lifetime.calc_lifetimes(
            self._accelerator, self._twiss, self._summary, Ne1C, coupling, pressure_profile)
        self._beam_charge.set_lifetimes(elastic=e_lifetime,
                                        inelastic=i_lifetime,
                                        quantum=q_lifetime,
                                        touschek_coefficient=t_coeff)

    def _incoming_bunch_injected_in_si(self, charge):
        rf_frequency = pyaccel.optics.get_rf_frequency(self._accelerator)
        bunch_offset = round(self._ti_delay * rf_frequency)
        harmonic_number = self.model_module.harmonic_number
        bunch_charge = [0.0] * harmonic_number
        for i in range(len(charge)):
            n = (i + bunch_offset) % harmonic_number
            bunch_charge[n] += charge[i]
        return bunch_charge
