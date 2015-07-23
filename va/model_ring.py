
import time
import os
import math
import numpy
import pyaccel
import mathphys
import va.utils as utils
from va.model import Model, TRACK6D, VCHAMBER, UNDEF_VALUE, _u


class RingModel(Model):

    def __init__(self, model_module, all_pvs=None, log_func=utils.log):
        # stored model state parameters
        super().__init__(model_module, all_pvs=all_pvs, log_func=log_func)
        self.reset('start', model_module.lattice_version)
        self._init_magnets_and_power_supplies()

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
        if '-BPM-' in pv_name:
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
        elif 'PS-' in pv_name:
            return self._power_supplies[pv_name].current
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

    def set_pv(self, pv_name, value):
        if self.set_pv_magnets(pv_name, value): return
        if self.set_pv_rf(pv_name, value): return
        if self.set_pv_fake(pv_name, value): return

    def set_pv_magnets(self, pv_name, value):
        ps = self._power_supplies[pv_name]
        prev_value = ps.current
        if value != prev_value:
            ps.current = value
            self._state_deprecated = True
        return True

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
            self._state_deprecated = False

        if force and self._model_module.lattice_version.startswith('BO'):
            # we need to check deprecation of other models on which booster depends

            # injection
            inj_parms = self._get_parameters_from_upstream_accelerator()
            inj_emittance = inj_parms['emittance']
            inj_energy_spread = inj_parms['energy_spread']
            inj_init_twiss = inj_parms['twiss_at_entrance']

            self._kickin_on()
            self._calc_injection_loss_fraction(inj_emittance, inj_energy_spread, inj_init_twiss)
            self._kickin_off()

            # acceleration
            self._calc_acceleration_loss_fraction()

            # ejection
            ext_parms = self._get_equilibrium_at_maximum_energy()
            ext_emittance = ext_parms['emittance']
            ext_energy_spread = ext_parms['energy_spread']
            ext_coupling = ext_parms['global_coupling']
            ext_init_twiss = self._twiss[self._kickex_idx[0]]

            self._kickex_on()
            self._calc_ejection_twiss(ext_init_twiss)
            self._calc_ejection_beam_size(ext_emittance, ext_energy_spread, ext_coupling)
            self._calc_ejection_loss_fraction()
            self._kickex_off()

    def reset(self, message1='reset', message2='', c='white', a=None):
        if self._all_pvs is None:
            self._record_names = self._model_module.record_names.get_record_names()
        else:
            self._record_names = self._all_pvs
        self._accelerator = self._model_module.create_accelerator()
        self._beam_charge  = None #utils.BeamCharge()
        self.beam_dump(message1,message2,c,a)

    def beam_init(self, message1='init', message2=None, c='white', a=None):
        if not message2:
            message2 = self._model_module.lattice_version
        self.beam_dump(message1,message2,c,a)

    def beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        self._state_deprecated = True
        if self._beam_charge: self._beam_charge.dump()
        self._closed_orbit = None
        self._twiss = None
        self._m66 = None
        self._transfer_matrices = None
        self._summary = None

    def beam_inject(self, delta_charge, message1='inject', message2 = '', c='white', a=None):
        if message1 and message1 != 'cycle':
            self._log(message1, message2, c=c, a=a)
        if self._summary is None: return
        if self._model_module.lattice_version.startswith('BO'):
            efficiency = 1.0 - self._injection_loss_fraction
        else:
            efficiency = 1.0
        delta_charge = [delta_charge_bunch * efficiency for delta_charge_bunch in delta_charge]
        self._beam_charge.inject(delta_charge)
        final_charge = self._beam_charge.value
        if message1 == 'cycle':
            self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency), c='white')
        return final_charge

    def beam_eject(self, message1='eject', message2 = '', c='white', a=None):
        if message1 and message1 != 'cycle':
            self._log(message1, message2, c=c, a=a)
        if self._model_module.lattice_version.startswith('BO'):
            efficiency = 1.0 - self._ejection_loss_fraction
        else:
            efficiency = 1.0
        charge = self._beam_charge.value
        final_charge = [charge_bunch * efficiency for charge_bunch in charge]
        self._beam_charge.dump()
        if message1 == 'cycle':
            self._log(message1 = 'cycle', message2 = 'beam ejection from {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency), c='white')
        return final_charge

    def beam_accelerate(self):
        if self._model_module.lattice_version.startswith('BO'):
            efficiency = 1.0 - self._acceleration_loss_fraction
        else:
            efficiency = 1.0
        final_charge = self._beam_charge.value
        self._log(message1 = 'cycle', message2 = 'beam acceleration at {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency))
        return final_charge

    # --- auxilliary methods

    def _get_elements_indices(self, pv_name):
        """Get flattened indices of element in the model"""
        data = self._record_names[pv_name]
        indices = []
        for key in data.keys():
            idx = mathphys.utils.flatten(data[key])
            indices.extend(idx)
        return indices

    def _calc_closed_orbit(self):
        # calcs closed orbit when there is beam
        try:
            self._log('calc', 'closed orbit for '+self._model_module.lattice_version)
            if TRACK6D:
                self._closed_orbit = pyaccel.tracking.findorbit6(self._accelerator, indices='open')
            else:
                self._closed_orbit = numpy.zeros((6,len(self._accelerator)))
                self._closed_orbit[:4,:] = pyaccel.tracking.findorbit4(self._accelerator, indices='open')
        except pyaccel.tracking.TrackingException:
            # beam is lost
            self.beam_dump('panic', 'BEAM LOST: closed orbit does not exist', c='red')

    def _calc_linear_optics(self):
        # calcs linear optics when there is beam
        if self._closed_orbit is None: return
        try:
            # optics
            self._log('calc', 'linear optics for '+self._model_module.lattice_version)
            self._twiss, self._m66, self._transfer_matrices, self._closed_orbit = \
                pyaccel.optics.calc_twiss(self._accelerator, fixed_point=self._closed_orbit[:,0])
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
                                         closed_orbit=self._closed_orbit)
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

    def _init_magnets_and_power_supplies(self):
        accelerator = self._accelerator
        accelerator_data = self._model_module.accelerator_data
        magnet_names = self._model_module.record_names.get_magnet_names()
        family_mapping = self._model_module.family_mapping
        excitation_curve_mapping = self._model_module.excitation_curves.get_excitation_curve_mapping()
        _, ps2magnet = self._model_module.power_supplies.get_magnet_mapping()

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
            if family_type == 'dipole':
                magnet = utils.DipoleMagnet(accelerator, indices, filename)
            elif family_type == 'quadrupole':
                magnet = utils.QuadrupoleMagnet(accelerator, indices, filename)
            elif family_type == 'sextupole':
                magnet = utils.SextupoleMagnet(accelerator, indices, filename)
            elif family_type in ('slow_horizontal_corrector', 'fast_horizontal_corrector', 'horizontal_corrector'):
                magnet = utils.HorizontalCorrectorMagnet(accelerator, indices, filename)
            elif family_type in ('slow_vertical_corrector', 'fast_vertical_corrector', 'vertical_corrector'):
                magnet = utils.VerticalCorrectorMagnet(accelerator, indices, filename)
            elif family_type == 'skew_quadrupole':
                magnet = utils.SkewQuadrupoleMagnet(accelerator, indices, filename)
            else:
                magnet = None

            if magnet is not None:
                self._magnets[magnet_name] = magnet

        # Set initial current values
        self._power_supplies = dict()
        for ps_name in ps2magnet.keys():
            magnets = set()
            for magnet_name in ps2magnet[ps_name]:
                if magnet_name in self._magnets:
                    magnets.add(self._magnets[magnet_name])
            if '-FAM' in ps_name:
                power_supply = utils.FamilyPowerSupply(magnets)
            else:
                power_supply = utils.IndividualPowerSupply(magnets)
            self._power_supplies[ps_name] = power_supply

    def _get_twiss(self, index):
        self.update_state()
        if isinstance(index, str):
            if index == 'end':
                return self._twiss[-1]
            elif index == 'begin':
                return self._twiss[0]
        else:
            return self._twiss[index]

    def _set_energy(energy):
        # need to update RF voltage !!!
        self._accelerator.energy = energy

    def _get_equilibrium_at_maximum_energy(self):
        return None

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

    def _calc_injection_loss_fraction(self, emittance, energy_spread, init_twiss):
        if init_twiss is None: return

        init_pos = init_twiss.fixed_point
        twiss,*_ = pyaccel.optics.calc_twiss(self._accelerator, init_twiss = init_twiss)
        betax , betay, etax, etay = pyaccel.optics.get_twiss(twiss, ('betax', 'betay', 'etax', 'etay'))

        if math.isnan(betax[-1]):
            self._injection_loss_fraction = 1.0
            return

        de = numpy.linspace(-(3*energy_spread), (3*energy_spread), 11)
        de_probability = numpy.zeros(len(de))
        lost_fraction = numpy.zeros(len(de))
        total_lost_fraction = 0

        for i in range(len(de)):
            de_probability[i] = math.exp(-(de[i]**2)/(2*(energy_spread**2)))/(math.sqrt(2*math.pi)*energy_spread)
            pos = [p for p in init_pos]
            pos[4] += de[i]
            orbit, *_ = pyaccel.tracking.linepass(self._accelerator, pos, indices = 'open')

            if math.isnan(orbit[0,-1]):
                lost_fraction[i] = 1.0
                total_lost_fraction += de_probability[i]*lost_fraction[i]
                continue

            rx, ry = orbit[[0,2],:]
            xlim_inf, xlim_sup = rx - self._hmin, self._hmax - rx
            ylim_inf, ylim_sup = ry - self._vmin, self._vmax - ry
            xlim_inf[xlim_inf < 0] = 0
            xlim_sup[xlim_sup < 0] = 0
            ylim_inf[ylim_inf < 0] = 0
            ylim_sup[ylim_sup < 0] = 0
            emit_x_inf = (xlim_inf**2  - (etax*energy_spread)**2)/betax
            emit_x_sup = (xlim_sup**2  - (etax*energy_spread)**2)/betax
            emit_y_inf = (ylim_inf**2  - (etay*energy_spread)**2)/betay
            emit_y_sup = (ylim_sup**2  - (etay*energy_spread)**2)/betay
            emit_x_inf[emit_x_inf < 0] = 0.0
            emit_x_sup[emit_x_sup < 0] = 0.0
            emit_y_inf[emit_y_inf < 0] = 0.0
            emit_y_sup[emit_y_sup < 0] = 0.0
            min_emit_x = numpy.amin([emit_x_inf, emit_x_sup])
            min_emit_y = numpy.amin([emit_y_inf, emit_y_sup])
            min_emit = min_emit_x + min_emit_y if min_emit_x*min_emit_y !=0 else 0.0
            lf = math.exp(- min_emit/emittance)
            lost_fraction[i] = lf if lf <1 else 1.0
            total_lost_fraction += de_probability[i]*lost_fraction[i]

        total_lost_fraction = total_lost_fraction/numpy.sum(de_probability)
        self._injection_loss_fraction = total_lost_fraction if total_lost_fraction < 1.0 else 1.0

    def _calc_acceleration_loss_fraction(self):
        self._acceleration_loss_fraction = 0.0

    def _calc_ejection_twiss(self, init_twiss):
        if init_twiss is None: return
        self._ejection_twiss, *_ = \
            pyaccel.optics.calc_twiss(self._accelerator[self._kickex_idx[0]:self._ext_point+1], init_twiss = init_twiss)

    def _calc_ejection_beam_size(self, emittance, energy_spread, coupling):
        if self._ejection_twiss is None: return
        betax, etax, betay, etay = pyaccel.optics.get_twiss(self._ejection_twiss, ('betax','etax','betay','etay'))
        emitx = emittance * 1 / (1 + coupling)
        emity = emittance * coupling / (1 + coupling)
        self._sigmax = numpy.sqrt(betax * emitx + (etax * energy_spread)**2)
        self._sigmay = numpy.sqrt(betay * emity + (etax * energy_spread)**2)

    def _calc_ejection_loss_fraction(self):
        if self._ejection_twiss is None: return

        hmin = self._hmin[self._kickex_idx[0]:self._ext_point+1]
        hmax = self._hmax[self._kickex_idx[0]:self._ext_point+1]
        vmin = self._vmin[self._kickex_idx[0]:self._ext_point+1]
        vmax = self._vmax[self._kickex_idx[0]:self._ext_point+1]

        h_vc = hmax - hmin
        v_vc = vmax - vmin
        rx, ry = pyaccel.optics.get_twiss(self._ejection_twiss, ('rx','ry'))
        xlim_inf, xlim_sup = rx - hmin, hmax - rx
        ylim_inf, ylim_sup = ry - vmin, vmax - ry
        xlim_inf[xlim_inf < 0] = 0
        xlim_sup[xlim_sup < 0] = 0
        ylim_inf[ylim_inf < 0] = 0
        ylim_sup[ylim_sup < 0] = 0
        xlim_inf[xlim_inf > h_vc] = 0
        xlim_sup[xlim_sup > h_vc] = 0
        ylim_inf[ylim_inf > v_vc] = 0
        ylim_sup[ylim_sup > v_vc] = 0
        min_xfrac_inf = numpy.amin(xlim_inf/self._sigmax)
        min_xfrac_sup = numpy.amin(xlim_sup/self._sigmax)
        min_yfrac_inf = numpy.amin(ylim_inf/self._sigmay)
        min_yfrac_sup = numpy.amin(ylim_sup/self._sigmay)
        sqrt2 = math.sqrt(2)
        x_surviving_fraction = 0.5*math.erf(min_xfrac_inf/sqrt2) + \
                               0.5*math.erf(min_xfrac_sup/sqrt2)
        y_surviving_fraction = 0.5*math.erf(min_yfrac_inf/sqrt2) + \
                               0.5*math.erf(min_yfrac_sup/sqrt2)
        surviving_fraction = x_surviving_fraction * y_surviving_fraction
        self._ejection_loss_fraction = 1.0 - surviving_fraction
