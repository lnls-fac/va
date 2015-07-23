
import math
import numpy
import pyaccel
import mathphys
import va.utils as utils
from va.model import TRACK6D, UNDEF_VALUE, _u
from va.accelerator_model import AcceleratorModel


class RingModel(AcceleratorModel):

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(all_pvs=all_pvs, log_func=log_func)

    # --- methods implementing response of model to get requests

    def get_pv_dynamic(self, pv_name):
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

    def get_pv_static(self, pv_name):
        # process global parameters
        value = super().get_pv_static(pv_name)
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

    def set_pv_rf(self, pv_name, value):
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
            self._injection_loss_fraction = 0.0
            self._ejection_loss_fraction = 0.0
            self._state_deprecated = False

        if force and self._model_module.lattice_version.startswith('BO'):
            # injection
            self._kickin_on()
            self._calc_injection_loss_fraction()
            self._kickin_off()
            # acceleration
            self._calc_acceleration_loss_fraction()
            # ejection
            self._kickex_on()
            self._calc_ejection_loss_fraction()
            self._kickex_off()

    def beam_dump(self, message1='panic', message2='', c='white', a=None):
        super().beam_dump(message1=message1, message2=message2, c=c, a=a)
        self._acceleration_loss_fraction = None

    # def beam_inject(self, delta_charge, message1='inject', message2 = '', c='white', a=None):
    #     if message1 and message1 != 'cycle':
    #         self._log(message1, message2, c=c, a=a)
    #     if self._summary is None: return
    #     if self._model_module.lattice_version.startswith('BO'):
    #         efficiency = 1.0 - self._injection_loss_fraction
    #     else:
    #         efficiency = 1.0
    #     delta_charge = [delta_charge_bunch * efficiency for delta_charge_bunch in delta_charge]
    #     self._beam_charge.inject(delta_charge)
    #     final_charge = self._beam_charge.value
    #     if message1 == 'cycle':
    #         self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency), c='white')
    #     return final_charge
    #
    # def beam_eject(self, message1='eject', message2 = '', c='white', a=None):
    #     if message1 and message1 != 'cycle':
    #         self._log(message1, message2, c=c, a=a)
    #     if self._model_module.lattice_version.startswith('BO'):
    #         efficiency = 1.0 - self._ejection_loss_fraction
    #     else:
    #         efficiency = 1.0
    #     charge = self._beam_charge.value
    #     final_charge = [charge_bunch * efficiency for charge_bunch in charge]
    #     self._beam_charge.dump()
    #     if message1 == 'cycle':
    #         self._log(message1 = 'cycle', message2 = 'beam ejection from {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency), c='white')
    #     return final_charge

    def beam_accelerate(self):
        if self._model_module.lattice_version.startswith('BO'):
            efficiency = 1.0 - self._acceleration_loss_fraction
        else:
            efficiency = 1.0
        final_charge = self._beam_charge.value
        self._log(message1 = 'cycle', message2 = 'beam acceleration at {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency))
        return final_charge

    # --- auxilliary methods

    def _calc_closed_orbit(self):
        # calcs closed orbit when there is beam
        try:
            self._log('calc', 'closed orbit for '+self._model_module.lattice_version)
            if TRACK6D:
                self._orbit = pyaccel.tracking.findorbit6(self._accelerator, indices='open')
            else:
                self._orbit = numpy.zeros((6,len(self._accelerator)))
                self._orbit[:4,:] = pyaccel.tracking.findorbit4(self._accelerator, indices='open')
        except pyaccel.tracking.TrackingException:
            # beam is lost
            self.beam_dump('panic', 'BEAM LOST: closed orbit does not exist', c='red')

    def _calc_linear_optics(self):
        # calcs linear optics when there is beam
        if self._orbit is None: return
        try:
            # optics
            self._log('calc', 'linear optics for '+self._model_module.lattice_version)
            self._twiss, self._m66, self._transfer_matrices, self._orbit = \
                pyaccel.optics.calc_twiss(self._accelerator, fixed_point=self._orbit[:,0])
        except numpy.linalg.linalg.LinAlgError:
            # beam is lost
            self.beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')
        except pyaccel.optics.OpticsException:
            # beam is lost
            self.beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')
        except pyaccel.tracking.TrackingException:
            # beam is lost
            self.beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')

    def _calc_equilibrium_parameters(self):
        if self._m66 is None: return
        try:
            self._log('calc', 'equilibrium parameters for '+self._model_module.lattice_version)
            self._summary, *_ = pyaccel.optics.get_equilibrium_parameters(\
                                         accelerator=self._accelerator,
                                         twiss=self._twiss,
                                         m66=self._m66,
                                         transfer_matrices=self._transfer_matrices,
                                         closed_orbit=self._orbit)
        except:
            self.beam_dump('panic', 'BEAM LOST: unable to calc equilibrium parameters', c='red')

    def _calc_lifetimes(self):
            if self._summary is None or self._beam_charge is None: return

            self._log('calc', 'beam lifetimes for '+self._model_module.lattice_version)

            Ne1C = 1.0/mathphys.constants.elementary_charge # number of electrons in 1 coulomb
            coupling = self._model_module.accelerator_data['global_coupling']
            pressure_profile = self._model_module.accelerator_data['pressure_profile']

            e_lifetime, i_lifetime, q_lifetime, t_coeff = pyaccel.lifetime.calc_lifetimes(self._accelerator,
                                                                self._twiss, self._summary, Ne1C, coupling, pressure_profile)
            self._beam_charge.set_lifetimes(elastic=e_lifetime,
                                            inelastic=i_lifetime,
                                            quantum=q_lifetime,
                                            touschek_coefficient=t_coeff)


    # def _calc_lifetimes(self):
    #     if self._summary is None or self._beam_charge is None: return
    #
    #     self._log('calc', 'beam lifetimes for '+self._model_module.lattice_version)
    #
    #     spos, pressure = self._model_module.accelerator_data['pressure_profile']
    #     avg_pressure = numpy.trapz(pressure,spos)/(spos[-1]-spos[0])
    #     spos, *betas = pyaccel.optics.get_twiss(self._twiss, ('spos', 'betax','betay'))
    #     alphax, etapx, *etas = pyaccel.optics.get_twiss(self._twiss, ('alphax', 'etapx','etax','etay'))
    #     energy = self._accelerator.energy
    #     e0 = self._summary['natural_emittance']
    #     k = self._model_module.accelerator_data['global_coupling']
    #     sigmae = self._summary['natural_energy_spread']
    #     sigmal = self._summary['bunch_length']
    #     Ne1C = 1.0/mathphys.constants.elementary_charge # number of electrons in 1 coulomb
    #     rad_damping_times = self._summary['damping_times']
    #
    #     # acceptances
    #     eaccep = self._summary['rf_energy_acceptance']
    #     accepx, accepy, *_ = pyaccel.optics.get_transverse_acceptance(
    #                                             self._accelerator,
    #                                             twiss=self._twiss, energy_offset=0.0)
    #     taccep = [min(accepx), min(accepy)]
    #
    #     lifetimes = self._beam_charge.get_lifetimes()
    #     thetax = numpy.sqrt(taccep[0]/betas[0])
    #     thetay = numpy.sqrt(taccep[1]/betas[1])
    #     R = thetay / thetax
    #     e_rate_spos = mathphys.beam_lifetime.calc_elastic_loss_rate(energy,R,taccep,avg_pressure,betas)
    #     t_rate_spos = mathphys.beam_lifetime.calc_touschek_loss_rate(energy,sigmae,e0,Ne1C,
    #             sigmal, k, (-eaccep,eaccep), betas, etas, alphax, etapx)
    #
    #     e_rate  = numpy.trapz(e_rate_spos,spos)/(spos[-1]-spos[0])
    #     i_rate  = mathphys.beam_lifetime.calc_inelastic_loss_rate(eaccep, pressure=avg_pressure)
    #     q_rate  = sum(mathphys.beam_lifetime.calc_quantum_loss_rates(e0, k, sigmae, taccep, eaccep, rad_damping_times))
    #     t_coeff = numpy.trapz(t_rate_spos,spos)/(spos[-1]-spos[0])
    #
    #     e_lifetime = float("inf") if e_rate == 0.0 else 1.0/e_rate
    #     i_lifetime = float("inf") if i_rate == 0.0 else 1.0/i_rate
    #     q_lifetime = float("inf") if q_rate == 0.0 else 1.0/q_rate
    #
    #     self._beam_charge.set_lifetimes(elastic=e_lifetime,
    #                                     inelastic=i_lifetime,
    #                                     quantum=q_lifetime,
    #                                     touschek_coefficient=t_coeff)


    def _set_energy(energy):
        # need to update RF voltage !!!
        self._accelerator.energy = energy

    def _kickin_on(self):
        for idx in self._kickin_idx:
            self._accelerator[idx].hkick_polynom = self._kickin_angle

    def _kickin_off(self):
        for idx in self._kickin_idx:
            self._accelerator[idx].hkick_polynom = 0.0

    def _kickex_on(self):
        for idx in self._kickex_idx:
            self._accelerator[idx].hkick_polynom = self._kickex_angle

    def _kickex_off(self):
        for idx in self._kickex_idx:
            self._accelerator[idx].hkick_polynom = 0.0

    def _calc_injection_loss_fraction(self):
        self._log('calc', 'injection efficiency  for '+self._model_module.lattice_version)
        inj_parms = self._get_parameters_from_upstream_accelerator()
        inj_parms['init_twiss'] = inj_parms.pop('twiss_at_entrance')
        args_dict = inj_parms
        args_dict.update(self._get_vacuum_chamber())
        args_dict.update(self._get_coordinate_system_parameters())
        self._injection_loss_fraction = utils.charge_loss_fraction_ring(self._accelerator, **args_dict)

    def _calc_acceleration_loss_fraction(self):
        self._acceleration_loss_fraction = 0.0

    def _calc_ejection_loss_fraction(self):
        if self._twiss is None: return
        self._log('calc', 'ejection efficiency  for '+self._model_module.lattice_version)

        accelerator = self._accelerator[self._kickex_idx[0]:self._ext_point+1]
        ejection_parameters = self._get_equilibrium_at_maximum_energy()
        args_dict = ejection_parameters
        args_dict.update(self._get_vacuum_chamber(init_idx=self._kickex_idx[0], final_idx=self._ext_point+1))
        self._ejection_loss_fraction, self._ejection_twiss, *_ = utils.charge_loss_fraction_line(accelerator,
            init_twiss=self._twiss[self._kickex_idx[0]], **args_dict)
