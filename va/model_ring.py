
from va.model import Model, TRACK6D, VCHAMBER, UNDEF_VALUE, _u
import va.utils as utils
import pyaccel
import numpy
import mathphys
import math


class RingModel(Model):

    def __init__(self, model_module, all_pvs=None, log_func=utils.log):
        # stored model state parameters
        super().__init__(model_module, all_pvs=all_pvs, log_func=log_func)
        self.reset('start', model_module.lattice_version)

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
        elif 'PS-CH' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            kickfield = 'hkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'hkick_polynom'
            kicks = pyaccel.lattice.get_attribute(self._accelerator, kickfield, idx)
            value = sum(kicks)
            return value
        elif 'PS-CV' in pv_name:
            idx = self._get_elements_indices(pv_name)
            kickfield = 'vkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'vkick_polynom'
            kicks = pyaccel.lattice.get_attribute(self._accelerator, kickfield, idx)
            value = sum(kicks)
            return value
        elif 'PS-QS' in pv_name:
            idx = self._get_elements_indices(pv_name)
            while not isinstance(idx, int): idx = idx[0]
            value = self._accelerator[idx].polynom_a[1]
            return value
        elif 'PS-Q' in pv_name:
            if '-FAM' in pv_name:
                value = self._quad_families_str[pv_name]
                return value
            else:
                idx = self._get_elements_indices(pv_name)
                pv_fam = '-'.join(pv_name.split('-')[:-1]) + '-FAM'
                try:
                    family_value = self._quad_families_str[pv_fam]
                except:
                    family_value = 0.0
                #print(family_value)
                value = self._accelerator[idx[0]].polynom_b[1] - family_value
                return value
        elif 'PS-S' in pv_name:
            if '-FAM' in pv_name:
                value = self._sext_families_str[pv_name]
                return value
            else:
                idx = self._get_elements_indices(pv_name)
                pv_fam = '-'.join(pv_name.split('-')[:-1]) + '-FAM'
                try:
                    family_value = self._sext_families_str[pv_fam]
                except:
                    family_value = 0.0
                value = self._accelerator[idx[0]].polynom_b[2] - family_value
                return value
        elif 'PS-BEND' in pv_name:
            return self._accelerator.energy
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

    # def get_pv_fake(self, pv_name):
    #     if 'FK-RESET' in pv_name:
    #         return 0.0
    #     elif 'FK-INJECT' in pv_name:
    #         return 0.0
    #     elif 'FK-DUMP' in pv_name:
    #         return 0.0
    #     else:
    #         return super().get_pv_fake(pv_name)

    # --- methods implementing response of model to set requests

    def set_pv(self, pv_name, value):
        if self.set_pv_correctors(pv_name, value): return
        if self.set_pv_quadrupoles_skew(pv_name, value): return  # has to be before quadrupoles
        if self.set_pv_quadrupoles(pv_name, value): return
        if self.set_pv_sextupoles(pv_name, value): return
        if self.set_pv_rf(pv_name, value): return
        if self.set_pv_fake(pv_name, value): return

    def set_pv_correctors(self, pv_name, value):

        if 'PS-CH' in pv_name:
            idx = self._get_elements_indices(pv_name)
            nr_segs = len(idx)
            kickfield = 'hkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'hkick_polynom'
            prev_value = nr_segs * getattr(self._accelerator[idx[0]], kickfield)
            if value != prev_value:
                pyaccel.lattice.set_attribute(self._accelerator, kickfield, idx, value/nr_segs)
                self._state_deprecated = True
            return True

        if 'PS-CV' in pv_name:
            idx = self._get_elements_indices(pv_name)
            nr_segs = len(idx)
            kickfield = 'vkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'vkick_polynom'
            prev_value = nr_segs * getattr(self._accelerator[idx[0]], kickfield)
            if value != prev_value:
                pyaccel.lattice.set_attribute(self._accelerator, kickfield, idx, value/nr_segs)
                self._state_deprecated = True
            return True

        return False  # [pv is not a corrector]

    def set_pv_quadrupoles_skew(self, pv_name, value):
        if 'PS-QS' in pv_name:
            indices = self._get_elements_indices(pv_name)
            prev_Ks = pyaccel.lattice.get_attribute(self._accelerator, 'polynom_a', indices, m=1)
            if value != prev_Ks[0]:
                for idx in indices:
                    self._accelerator[idx].polynom_a[1] = value
                self._state_deprecated = True
            return True
        return False

    def set_pv_quadrupoles(self, pv_name, value):

        if 'PS-Q' in pv_name:
            if '-FAM' in pv_name:
                # family PV
                prev_family_value = self._quad_families_str[pv_name]
                if value != prev_family_value:
                    self._quad_families_str[pv_name] = value
                    data = self._record_names[pv_name]
                    for fam_name in data.keys():
                        indices = data[fam_name]
                        for idx in indices:
                            if isinstance(idx,int): idx = [idx]
                            for idx2 in idx:
                                prev_total_value = self._accelerator[idx2].polynom_b[1]
                                prev_quad_value = prev_total_value - prev_family_value
                                new_total_value = value + prev_quad_value
                                self._accelerator[idx2].polynom_b[1] = new_total_value
                    self._state_deprecated = True
            else:
                # individual quad PV
                idx = self._get_elements_indices(pv_name)
                idx2 = idx
                while not isinstance(idx2,int):
                    idx2 = idx2[0]
                try:
                    fam_pv = '-'.join(pv_name.split('-')[:-1])+'-FAM'
                    family_value = self._sext_families_str[fam_pv]
                except:
                    family_value = 0.0
                prev_total_value = self._accelerator[idx2].polynom_b[1]
                prev_quad_value = prev_total_value - family_value
                if value != prev_quad_value:
                    if isinstance(idx,int): idx = [idx]
                    for i in idx:
                        self._accelerator[i].polynom_b[1] = value + family_value
                    self._state_deprecated = True
            return True

        return False # [pv is not a quadrupole]

    def set_pv_sextupoles(self, pv_name, value):

        if 'PS-S' in pv_name:
            if '-FAM' in pv_name:
                # family PV
                prev_family_value = self._sext_families_str[pv_name]
                if value != prev_family_value:
                    self._sext_families_str[pv_name] = value
                    data = self._record_names[pv_name]
                    for fam_name in data.keys():
                        indices = data[fam_name]
                        for idx in indices:
                            if isinstance(idx,int): idx = [idx]
                            for idx2 in idx:
                                prev_total_value = self._accelerator[idx2].polynom_b[2]
                                prev_sext_value = prev_total_value - prev_family_value
                                new_total_value = value + prev_sext_value
                                self._accelerator[idx2].polynom_b[2] = new_total_value
                    self._state_deprecated = True
            else:
                # individual sext PV
                idx = self._get_elements_indices(pv_name)
                idx2 = idx
                while not isinstance(idx2,int):
                    idx2 = idx2[0]
                try:
                    fam_pv = '-'.join(pv_name.split('-')[:-1])+'-FAM'
                    family_value = self._sext_families_str[fam_pv]
                except:
                    family_value = 0.0
                prev_total_value = self._accelerator[idx2].polynom_b[2]
                prev_sext_value = prev_total_value - family_value
                if value != prev_sext_value:
                    if isinstance(idx,int): idx = [idx]
                    for i in idx:
                        self._accelerator[i].polynom_b[2] = value + family_value
                    self._state_deprecated = True
            return True

        return False # [pv is not a sextupole]

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

    # def set_pv_fake(self, pv_name, value):
    #     if super().set_pv_fake(pv_name, value): return
    #     if 'FK-RESET' in pv_name:
    #         print('set fk reset')
    #         self.reset(message1='reset',message2=self._model_module.lattice_version)
    #         return True
    #     elif 'FK-INJECT' in pv_name:
    #         print('set fk inject')
    #         charge = value * _u.mA * _Tp(self._accelerator)
    #         self.beam_inject(charge, message1='inject', message2 = str(value)+' mA', c='green')
    #         return True
    #     elif 'FK-DUMP' in pv_name:
    #         print('set fk dump')
    #         self.beam_dump(message1='dump',message2='beam at ' + self._model_module.lattice_version)
    #         return True
    #     return False

    # --- methods that help updating the model state

    def update_state(self, force=False):
        if force or self._state_deprecated:
            self._calc_closed_orbit()
            self._calc_linear_optics()
            self._calc_equilibrium_parameters()
            self._calc_lifetimes()
            self._state_deprecated = False

    def reset(self, message1='reset', message2='', c='white', a=None):
        if self._all_pvs is None:
            self._record_names = self._model_module.record_names.get_record_names()
        else:
            self._record_names = self._all_pvs
        self._accelerator = self._model_module.create_accelerator()
        self._beam_charge  = None #utils.BeamCharge()
        self._quad_families_str = {}
        self._sext_families_str = {}
        self.beam_dump(message1,message2,c,a)
        #self.update_state(force=True)

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
        init_charge = self._beam_charge.value
        self._beam_charge.inject(delta_charge)
        final_charge = self._beam_charge.value
        #print(sum(init_charge))
        #print(sum(final_charge))
        #print(sum(delta_charge))
        efficiency = (sum(final_charge) - sum(init_charge))/sum(delta_charge)
        if message1 == 'cycle':
            self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency), c='white')
        #self.update_state()
        return final_charge

    def beam_eject(self, message1='eject', message2 = '', c='white', a=None):
        if message1 and message1 != 'cycle':
            self._log(message1, message2, c=c, a=a)
        init_charge = self._beam_charge.value
        final_charge = self._beam_charge.value
        self._beam_charge.dump()
        efficiency = sum(final_charge)/sum(init_charge)
        if message1 == 'cycle':
            self._log(message1 = 'cycle', message2 = 'beam ejection from {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency), c='white')
        return final_charge

    def beam_accelerate(self):
        efficiency = 1.0
        self._log(message1 = 'cycle', message2 = 'beam acceleration at {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency))
        charge = self._beam_charge.value
        return charge

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

        spos, pressure = self._model_module.accelerator_data['pressure_profile']
        avg_pressure = numpy.trapz(pressure,spos)/(spos[-1]-spos[0])
        spos, *betas = pyaccel.optics.get_twiss(self._twiss, ('spos', 'betax','betay'))
        alphax, etapx, *etas = pyaccel.optics.get_twiss(self._twiss, ('alphax', 'etapx','etax','etay'))
        energy = self._accelerator.energy
        e0 = self._summary['natural_emittance']
        k = self._model_module.accelerator_data['global_coupling']
        sigmae = self._summary['natural_energy_spread']
        sigmal = self._summary['bunch_length']
        Ne1C = 1.0/mathphys.constants.elementary_charge # number of electrons in 1 coulomb
        rad_damping_times = self._summary['damping_times']

        # acceptances
        eaccep = self._summary['rf_energy_acceptance']
        accepx, accepy, *_ = pyaccel.optics.get_transverse_acceptance(
                                                self._accelerator,
                                                twiss=self._twiss, energy_offset=0.0)
        taccep = [min(accepx), min(accepy)]

        lifetimes = self._beam_charge.get_lifetimes()
        thetax = numpy.sqrt(taccep[0]/betas[0])
        thetay = numpy.sqrt(taccep[1]/betas[1])
        R = thetay / thetax
        e_rate_spos = mathphys.beam_lifetime.calc_elastic_loss_rate(energy,R,taccep,avg_pressure,betas)
        t_rate_spos = mathphys.beam_lifetime.calc_touschek_loss_rate(energy,sigmae,e0,Ne1C,
                sigmal, k, (-eaccep,eaccep), betas, etas, alphax, etapx)

        e_rate  = numpy.trapz(e_rate_spos,spos)/(spos[-1]-spos[0])
        i_rate  = mathphys.beam_lifetime.calc_inelastic_loss_rate(eaccep, pressure=avg_pressure)
        q_rate  = sum(mathphys.beam_lifetime.calc_quantum_loss_rates(e0, k, sigmae, taccep, eaccep, rad_damping_times))
        t_coeff = numpy.trapz(t_rate_spos,spos)/(spos[-1]-spos[0])

        e_lifetime = float("inf") if e_rate == 0.0 else 1.0/e_rate
        i_lifetime = float("inf") if i_rate == 0.0 else 1.0/i_rate
        q_lifetime = float("inf") if q_rate == 0.0 else 1.0/q_rate

        # print('elastic     [h]:', e_lifetime/3600)
        # print('inelastic   [h]:', i_lifetime/3600)
        # print('quantum     [h]:', q_lifetime/3600)
        # print('touschek [1/sC]:', t_coeff)

        self._beam_charge.set_lifetimes(elastic=e_lifetime,
                                        inelastic=i_lifetime,
                                        quantum=q_lifetime,
                                        touschek_coefficient=t_coeff)

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

    def _init_families_str(self):
        rnames = self._record_names
        for pv_name in rnames.keys():
            if '-FAM' in pv_name:
                if 'PS-Q' in pv_name:
                    idx = self._get_elements_indices(pv_name)
                    value = self._accelerator[idx[0]].polynom_b[1]
                    self._quad_families_str[pv_name] = value
                if 'PS-S' in pv_name:
                    idx = self._get_elements_indices(pv_name)
                    try:
                        value = self._accelerator[idx[0]].polynom_b[2]
                    except:
                        # print(idx)
                        raise Exception('problem!')
                    self._sext_families_str[pv_name] = value
