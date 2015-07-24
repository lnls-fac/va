
import math
import numpy
import pyaccel
import mathphys
import va.utils as utils
from va.model_accelerator import AcceleratorModel, TRACK6D, UNDEF_VALUE, _u


class RingModel(AcceleratorModel):

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(all_pvs=all_pvs, log_func=log_func)

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
                if self._closed_orbit is None or charge == 0.0: return [UNDEF_VALUE]*len(idx)
                return self._closed_orbit[0,idx]
            elif 'FAM-Y' in pv_name:
                if self._closed_orbit is None or charge == 0.0: return [UNDEF_VALUE]*len(idx)
                return self._closed_orbit[2,idx]
            else:
                if self._closed_orbit is None or charge == 0.0: return [UNDEF_VALUE]*2
                return self._closed_orbit[[0,2],idx[0]]
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

    def update_state(self, force=False):
        if force or self._state_deprecated:
            self._calc_closed_orbit()
            self._calc_linear_optics()
            self._calc_equilibrium_parameters()
            self._calc_lifetimes()
            self._state_deprecated = False
            if self._prefix == 'BO':
                # injection
                self._set_kickin('on')
                self._calc_injection_loss_fraction()
                self._set_kickin('off')
                # acceleration
                self._calc_acceleration_loss_fraction()
                # ejection
                self._set_kickex('on')
                self._calc_ejection_loss_fraction()
                self._set_kickex('off')
                # signaling deprecation for other models
                self._driver.ts_model._upstream_accelerator_state_deprecated = True

        if self._prefix=='BO' and self._upstream_accelerator_state_deprecated:
            self._upstream_accelerator_state_deprecated = False
            # injection
            self._set_kickin('on')
            self._calc_injection_loss_fraction()
            self._set_kickin('off')

    def beam_accelerate(self):
        self.update_state()
        efficiency = 1.0 - self._acceleration_loss_fraction
        charge = self._beam_charge.value
        final_charge = list(numpy.multiply(charge, efficiency))
        self._beam_charge.dump()
        self._beam_charge.inject(final_charge)
        return efficiency

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        super()._beam_dump(message1=message1, message2=message2, c=c, a=a)
        if self._prefix == 'BO':
            self._injection_loss_fraction    = None
            self._acceleration_loss_fraction = None
            self._ejection_loss_fraction     = None
        else:
            self._acceleration_loss_fraction = 0.0

    # --- auxilliary methods

    def _calc_closed_orbit(self):
        # calcs closed orbit when there is beam
        try:
            self._log('calc', 'closed orbit for ' + self._prefix)
            if TRACK6D:
                self._closed_orbit = pyaccel.tracking.findorbit6(self._accelerator, indices='open')
            else:
                self._closed_orbit = numpy.zeros((6,len(self._accelerator)))
                self._closed_orbit[:4,:] = pyaccel.tracking.findorbit4(self._accelerator, indices='open')
        except pyaccel.tracking.TrackingException:
            # beam is lost
            self._beam_dump('panic', 'BEAM LOST: closed orbit does not exist', c='red')

    def _calc_linear_optics(self):
        # calcs linear optics when there is beam
        if self._closed_orbit is None: return
        try:
        # optics
            self._log('calc', 'linear optics for ' + self._prefix)
            self._twiss, self._m66, self._transfer_matrices, self._closed_orbit = \
                pyaccel.optics.calc_twiss(self._accelerator, fixed_point=self._closed_orbit[:,0])
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
            self._log('calc', 'equilibrium parameters for ' + self._prefix)
            self._summary, *_ = pyaccel.optics.get_equilibrium_parameters(\
                                         accelerator=self._accelerator,
                                         twiss=self._twiss,
                                         m66=self._m66,
                                         transfer_matrices=self._transfer_matrices,
                                         closed_orbit=self._closed_orbit)
        except:
            self._beam_dump('panic', 'BEAM LOST: unable to calc equilibrium parameters', c='red')

    def _calc_lifetimes(self):
            if self._summary is None or self._beam_charge is None: return

            self._log('calc', 'beam lifetimes for ' + self._prefix)

            Ne1C = 1.0/mathphys.constants.elementary_charge # number of electrons in 1 coulomb
            coupling = self._model_module.accelerator_data['global_coupling']
            pressure_profile = self._model_module.accelerator_data['pressure_profile']

            e_lifetime, i_lifetime, q_lifetime, t_coeff = pyaccel.lifetime.calc_lifetimes(self._accelerator,
                                                                self._twiss, self._summary, Ne1C, coupling, pressure_profile)
            self._beam_charge.set_lifetimes(elastic=e_lifetime,
                                            inelastic=i_lifetime,
                                            quantum=q_lifetime,
                                            touschek_coefficient=t_coeff)

    def _set_energy(energy):
        # need to update RF voltage !!!
        self._accelerator.energy = energy

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

    def _calc_injection_loss_fraction(self):
        self._log('calc', 'injection efficiency  for '+ self._prefix)
        args_dict = self._get_parameters_from_upstream_accelerator()
        args_dict.update(self._get_vacuum_chamber())
        args_dict.update(self._get_coordinate_system_parameters())
        self._injection_loss_fraction = utils.charge_loss_fraction_ring(self._accelerator, **args_dict)

    def _calc_acceleration_loss_fraction(self):
        self._log('calc', 'acceleration efficiency  for '+ self._prefix)
        self._acceleration_loss_fraction = 0.0

    def _calc_ejection_loss_fraction(self):
        if self._twiss is None: return
        self._log('calc', 'ejection efficiency  for '+ self._prefix)
        accelerator = self._accelerator[self._kickex_idx[0]:self._ext_point+1]
        init_twiss = self._twiss[self._kickex_idx[0]]
        args_dict = self._get_equilibrium_at_maximum_energy()
        args_dict.update(self._get_vacuum_chamber(init_idx=self._kickex_idx[0], final_idx=self._ext_point+1))
        self._ejection_loss_fraction, self._ejection_twiss, *_ = \
            utils.charge_loss_fraction_line(accelerator, init_twiss = init_twiss, **args_dict)
