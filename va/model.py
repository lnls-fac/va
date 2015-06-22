
"""Accelerator model module

The Model class in this module is in charge of the initialisation and
interaction with the engine (pyaccel/trackcpp). It updates values and
recalculates necessary parameters, controlling concurrent accesses coming from
the server.
"""

import time
import pyaccel
import sirius
import va.utils as utils
import numpy
import math
import lnls.utils
import datetime
import mathphys


TRACK6D     = False
VCHAMBER    = False
UNDEF_VALUE = 0.0

_u, _Tp = mathphys.units, pyaccel.optics.getrevolutionperiod


#--- general model classes ---#

class Model(object):

    def __init__(self, model_module=None, all_pvs=None, log_func=utils.log):
        # stored model state parameters
        self._driver = None # this will be set latter by Driver
        self._model_module = model_module
        self._log = log_func
        self._all_pvs = all_pvs

    def signal_all_models_set(self):
        pass

    def get_pv(self, pv_name):
        value = self.get_pv_dynamic(pv_name)
        if value is None:
            #print('try static: ' + pv_name + ' ', end='')
            value = self.get_pv_static(pv_name)
            #print(value)
        if value is None:
            #print('try fake: ' + pv_name)
            value = self.get_pv_fake(pv_name)
        if value is None:
            raise Exception('response to ' + pv_name + ' not implemented in model get_pv')
        return value

    def set_pv(self, pv_name, value):
        return None

    def get_pv_dynamic(self, pv_name):
        return None

    def get_pv_static(self, pv_name):
        return None

    def get_pv_fake(self, pv_name):
        return None

    def update_state(self):
        pass


class RingModel(Model):

    def __init__(self, model_module, all_pvs=None, log_func=utils.log):
        # stored model state parameters
        super().__init__(model_module, all_pvs=all_pvs, log_func=log_func)
        self.reset('start', model_module.lattice_version)

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
        self.update_state(force=True)

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

    def beam_inject(self, charge, message1='inject', message2 = '', c='white', a=None):
        if message1:
            self._log(message1, message2, c=c, a=a)
        if self._summary is None: return
        self._beam_charge.inject(charge)
        self.update_state()
        return self._beam_charge.value

    def beam_eject(self, message1='eject', message2 = '', c='white', a=None):
        if message1:
            self._log(message1, message2, c=c, a=a)
        charge = self._beam_charge.value
        self._beam_charge.dump()
        return charge

    def beam_charge(self):
        self.update_state()
        return self._beam_charge.total_value

    def beam_accelerate(self):
        charge = self._beam_charge.value
        return charge

    def _get_elements_indices(self, pv_name):
        """Get flattened indices of element in the model"""
        data = self._record_names[pv_name]
        indices = []
        for key in data.keys():
            idx = lnls.utils.flatten(data[key])
            indices.extend(idx)
        return indices

    def get_pv_fake(self, pv_name):
        if '-ERRORX' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            error = pyaccel.lattice.get_error_misalignment_x(self._accelerator, idx[0])
            return error
        if '-ERRORY' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            error = pyaccel.lattice.get_error_misalignment_y(self._accelerator, idx[0])
            return error
        elif 'FK-' in pv_name:
            return 0.0
        else:
            return None

    def get_pv_dynamic(self, pv_name):
        if 'DI-CURRENT' in pv_name:
            time_interval = pyaccel.optics.getrevolutionperiod(self._accelerator)
            currents = self._beam_charge.current(time_interval)
            currents_mA = [bunch_current / _u.mA for bunch_current in currents]
            return sum(currents_mA)
        elif 'DI-BCURRENT' in pv_name:
            time_interval = pyaccel.optics.getrevolutionperiod(self._accelerator)
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
            kicks = pyaccel.lattice.getattributelat(self._accelerator, kickfield, idx)
            value = sum(kicks)
            return value
        elif 'PS-CV' in pv_name:
            idx = self._get_elements_indices(pv_name)
            kickfield = 'vkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'vkick_polynom'
            kicks = pyaccel.lattice.getattributelat(self._accelerator, kickfield, idx)
            value = sum(kicks)
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
        elif 'PS-QS' in pv_name:
            idx = self._get_elements_indices(pv_name)
            while not isinstance(idx, int): idx = idx[0]
            value = self._accelerator[idx].polynom_a[1]
            return value
        elif 'RF-FREQUENCY' in pv_name:
            return pyaccel.optics.getrffrequency(self._accelerator)
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

    def set_pv(self, pv_name, value):
        if self.set_pv_correctors(pv_name, value): return
        if self.set_pv_quadrupoles_skew(pv_name, value): return  # has to be before quadrupoles
        if self.set_pv_quadrupoles(pv_name, value): return
        if self.set_pv_sextupoles(pv_name, value): return
        if self.set_pv_rf(pv_name, value): return
        if self.set_pv_fake(pv_name, value): return

    def set_pv_rf(self, pv_name, value):
        if 'RF-VOLTAGE' in pv_name:
            idx = self._get_elements_indices(pv_name)
            prev_value = self._accelerator[idx[0]].voltage
            if value != prev_value:
                self._accelerator[idx[0]].voltage = value
                self._state_deprecated = True
            return True
        elif 'RF-FREQUENCY' in pv_names:
            idx = self._get_elements_indices(pv_name)
            prev_value = self._accelerator[idx[0]].frequency
            if value != prev_value:
                self._accelerator[idx[0]].frequency = value
                self._state_deprecated = True
            return True
        return False

    def set_pv_fake(self, pv_name, value):
        if 'FK-RESET' in pv_name:
            self.reset(message1='reset',message2=self._model_module.lattice_version)
        elif 'FK-INJECT' in pv_name:
            charge = value * _u.mA * _Tp(self._accelerator)
            self.beam_inject(charge, message1='inject', message2 = str(value)+' mA', c='green')
        elif 'FK-DUMP' in pv_name:
            self.beam_dump(message1='dump',message2='beam at ' + self._model_module.lattice_version)
        elif '-ERRORX' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorx = pyaccel.lattice.get_error_misalignment_x(self._accelerator, idx[0])
            if value != prev_errorx:
                pyaccel.lattice.set_error_misalignment_x(self._accelerator, idx, value)
                self._state_deprecated = True
        elif '-ERRORY' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorx = pyaccel.lattice.get_error_misalignment_y(self._accelerator, idx[0])
            if value != prev_errorx:
                pyaccel.lattice.set_error_misalignment_y(self._accelerator, idx, value)
                self._state_deprecated = True

    def set_pv_quadrupoles_skew(self, pv_name, value):
        if 'PS-Q' in pv_name:
            indices = self._get_elements_indices(pv_name)
            prev_Ks = pyaccel.lattice.getattributelat(self._accelerator, 'polynom_a', indices, m=1)
            if value != prev_Ks[0]:
                for idx in indices:
                    self._accelerator[idx].polynom_a[1] = value
                self._state_deprecated = True
            return True
        return False

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

    def set_pv_correctors(self, pv_name, value):

        if 'PS-CH' in pv_name:
            idx = self._get_elements_indices(pv_name)
            nr_segs = len(idx)
            kickfield = 'hkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'hkick_polynom'
            prev_value = nr_segs * getattr(self._accelerator[idx[0]], kickfield)
            if value != prev_value:
                pyaccel.lattice.setattributelat(self._accelerator, kickfield, idx, value/nr_segs)
                self._state_deprecated = True
            return True

        if 'PS-CV' in pv_name:
            idx = self._get_elements_indices(pv_name)
            nr_segs = len(idx)
            kickfield = 'vkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'vkick_polynom'
            prev_value = nr_segs * getattr(self._accelerator[idx[0]], kickfield)
            if value != prev_value:
                pyaccel.lattice.setattributelat(self._accelerator, kickfield, idx, value/nr_segs)
                self._state_deprecated = True
            return True

        return False  # [pv is not a corrector]

    def update_state(self, force=False):

        if force or self._state_deprecated:
            self._calc_closed_orbit()
            self._calc_linear_optics()
            self._calc_equilibrium_parameters()
            self._calc_lifetimes()
            self._state_deprecated = False

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
                pyaccel.optics.calctwiss(self._accelerator, fixed_point=self._closed_orbit[:,0])
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
            self._summary, *_ = pyaccel.optics.getequilibriumparameters(\
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

        spos, *betas = pyaccel.optics.gettwiss(self._twiss, ('spos', 'betax','betay'))
        alphax, etaxl, *etas = pyaccel.optics.gettwiss(self._twiss, ('alphax', 'etaxl','etax','etay'))
        energy = self._accelerator.energy
        e0 = self._summary['natural_emittance']
        k = self._model_module.global_coupling
        sigmae = self._summary['natural_energy_spread']
        sigmal = self._summary['bunchlength']
        Ne1C = 1.0/mathphys.constants.elementary_charge # number of electrons in 1 coulomb
        rad_damping_times = self._summary['damping_times']
        avg_pressure = self._model_module.average_pressure
        # acceptances
        eaccep = self._summary['rf_energy_acceptance']
        accepx, accepy, *_ = pyaccel.optics.gettransverseacceptance(
                                                self._accelerator,
                                                twiss=self._twiss, energy_offset=0.0)
        taccep = [min(accepx), min(accepy)]

        lifetimes = self._beam_charge.get_lifetimes()
        thetax = numpy.sqrt(taccep[0]/betas[0])
        thetay = numpy.sqrt(taccep[1]/betas[1])
        R = thetay / thetax
        e_rate_spos = mathphys.beam_lifetime.calc_elastic_loss_rate(energy,R,taccep,avg_pressure,betas)
        t_rate_spos = mathphys.beam_lifetime.calc_touschek_loss_rate(energy,sigmae,e0,Ne1C,
                sigmal, k, (-eaccep,eaccep), betas, etas, alphax, etaxl)

        e_rate  = numpy.trapz(e_rate_spos,spos)/(spos[-1]-spos[0])
        i_rate  = mathphys.beam_lifetime.calc_inelastic_loss_rate(eaccep, pressure=avg_pressure)
        q_rate  = sum(mathphys.beam_lifetime.calc_quantum_loss_rates(e0, k, sigmae, taccep, eaccep, rad_damping_times))
        t_coeff = numpy.trapz(t_rate_spos,spos)/(spos[-1]-spos[0])

        e_lifetime = float("inf") if e_rate == 0.0 else 1.0/e_rate
        i_lifetime = float("inf") if i_rate == 0.0 else 1.0/i_rate
        q_lifetime = float("inf") if q_rate == 0.0 else 1.0/q_rate

        #print('elastic     [h]:', e_lifetime/3600)
        #print('inelastic   [h]:', i_lifetime/3600)
        #print('quantum     [h]:', q_lifetime/3600)
        #print('touschek [1/sC]:', t_coeff)

        self._beam_charge.set_lifetimes(elastic=e_lifetime,
                                        inelastic=i_lifetime,
                                        quantum=q_lifetime,
                                        touschek_coefficient=t_coeff)

    def _get_twiss(self, index):
        self.update_state()
        if isinstance(index, str):
            if index == 'last':
                return self._twiss[-1]
            elif index == 'first':
                return self._twiss[0]
        else:
            return self._twiss[index]

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
                        print(idx)
                        raise Exception('problem!')
                    self._sext_families_str[pv_name] = value


class TLineModel(Model):

    def __init__(self, model_module, all_pvs=None, log_func=utils.log):

        super().__init__(model_module=model_module, all_pvs=all_pvs, log_func=log_func)
        self.reset('start')

    def reset(self, message1='reset', message2='', c='white', a=None):
        if self._all_pvs is None:
            self._record_names = self._model_module.record_names.get_record_names()
        else:
            self._record_names = self._all_pvs
        self._accelerator = self._model_module.create_accelerator()
        self._beam_charge  = utils.BeamCharge()
        self._orbit = None
        self._twiss = None
        if not message2:
            message2 = self._model_module.lattice_version
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        self._state_deprecated = False

    def update_state(self, force=False):
        if force or self._state_deprecated:
            init_twiss = self.get_init_twiss()
            self._calc_orbit(init_twiss)
            self._calc_linear_optics(init_twiss)
            self._calc_beam_size()
            self._state_deprecated = False

    def beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        self._state_deprecated = True
        self._beam_charge.dump()
        self._orbit = None

    def beam_inject(self, charge, message1='inject', message2 = '', c='white', a=None):
        if message1:
            self._log(message1, message2, c=c, a=a)
        self._beam_charge.inject(charge)

    def beam_charge(self):
        return self._beam_charge.total_value

    def get_init_twiss(self):
        """Return initial Twiss parameters to be tracked"""
        return None

    def _calc_orbit(self, init_twiss):
        if init_twiss is None: return
        init_pos = init_twiss.fixed_point
        try:
            self._log('calc', 'orbit for '+self._model_module.lattice_version)
            self._orbit, *_ = pyaccel.tracking.linepass(self._accelerator, init_pos, indices = 'closed')
        except pyaccel.tracking.TrackingException:
            # beam is lost
            self.beam_dump('panic', 'BEAM LOST: orbit does not exist', c='red')

    def _calc_linear_optics(self, init_twiss):
        if init_twiss is None: return
        try:
            self._log('calc', 'linear optics for '+self._model_module.lattice_version)
            self._twiss, *_ = pyaccel.optics.calctwiss(self._accelerator, init_twiss=init_twiss)
        except pyaccel.tracking.TrackingException:
            self.beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')

    def _calc_beam_size(self):
        pass

    def _get_elements_indices(self, pv_name):
        """Get flattened indices of element in the model"""
        data = self._record_names[pv_name]
        indices = []
        for key in data.keys():
            idx = lnls.utils.flatten(data[key])
            indices.extend(idx)
        return indices

    def beam_transport(self, charge):

        self.update_state(force = True)
        # self._orbit = pyaccel.tracking.linepass(self._accelerator, self._rin, indices = 'open')[0]
        # try:
        #     self._rout = [i for i in self._orbit[:,(len(self._accelerator)-1)]]
        # except IndexError:
        #     self._rout = [0,0,0,0,0,0]
        # self.coordinate_transformation()
        # new_charge = charge*self._calc_loss_charge()
        loss_factor = self._calc_loss_charge()
        new_charge = [charge_bunch * loss_factor for charge_bunch in charge]
        self._beam_charge.inject(new_charge)
        return new_charge

    def coordinate_transformation(self):
        r = [i for i in self._rout]
        self._rout[0] = r[0]*math.cos(self._xl_out) + r[5]*math.sin(self._xl_out) + self._x_out
        self._rout[1] = r[1] + self._xl_out
        self._rout[5] = r[5]*math.cos(self._xl_out) - r[0]*math.sin(self._xl_out)

    def _calc_loss_charge(self):
        return 1.0 # !!! TEST
        try:
            orbit = [math.fabs(i) for i in self._orbit[0,:]]
            xmax = numpy.amax(orbit)
            ind_xmax = numpy.argmax(orbit)
            hmax = self._accelerator[ind_xmax].hmax
        except:
            return 1
        sigma_x = self._sigma_x[ind_xmax]
        frac = (1.0/2.0)*(math.erf((hmax+xmax)/(math.sqrt(2.0)*sigma_x))-math.erf((-hmax+xmax)/(math.sqrt(2.0)*sigma_x)))
        return frac

    def get_pv_fake(self, pv_name):
        if '-ERRORX' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            error = pyaccel.lattice.get_error_misalignment_x(self._accelerator, idx[0])
            return error
        if '-ERRORY' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            error = pyaccel.lattice.get_error_misalignment_y(self._accelerator, idx[0])
            return error
        elif 'FK-' in pv_name:
            return 0.0
        else:
            return None

    def get_pv_dynamic(self, pv_name):
        if 'DI-CURRENT' in pv_name:
            return 0
        else:
            return None

    def get_pv_static(self, pv_name):
        # process global parameters
        if '-BPM-' in pv_name:
            idx = self._get_elements_indices(pv_name)
            try:
                pos = self._orbit[[0,2],idx[0]]
            except:
                pos = UNDEF_VALUE, UNDEF_VALUE
            return pos
        elif 'PS-CH' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            kickfield = 'hkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'hkick_polynom'
            kicks = pyaccel.lattice.getattributelat(self._accelerator, kickfield, idx)
            value = sum(kicks)
            return value
        elif 'PS-CV' in pv_name:
            idx = self._get_elements_indices(pv_name)
            kickfield = 'vkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'vkick_polynom'
            kicks = pyaccel.lattice.getattributelat(self._accelerator, kickfield, idx)
            value = sum(kicks)
            return value
        elif 'PS-Q' in pv_name:
            idx = self._get_elements_indices(pv_name)
            value = self._accelerator[idx[0]].polynom_b[1]
            return value
        elif 'PS-BEND-' in pv_name or 'PU-SEP' in pv_name:
            idx = self._get_elements_indices(pv_name)
            value = 0
            for i in idx:
                value += self._accelerator[i].polynom_b[0]*self._accelerator[i].length
                value += self._accelerator[i].angle
            return value
        else:
            return None

    def set_pv(self, pv_name, value):
        if self.set_pv_correctors(pv_name, value): return
        if self.set_pv_quadrupoles(pv_name, value): return
        if self.set_pv_bends(pv_name, value): return
        if self.set_pv_fake(pv_name, value): return

    def set_pv_fake(self, pv_name, value):
        if 'FK-RESET' in pv_name:
            self.reset(message1='reset',message2=self._model_module.lattice_version)
        if 'FK-INJECT' in pv_name:
            charge = value * _u.mA * _Tp(self._accelerator)
            self.beam_inject(charge, message1='inject', message2 = str(value)+' mA', c='green')
        elif 'FK-DUMP' in pv_name:
            self.beam_dump(message1='dump',message2='beam at ' + self._model_module.lattice_version)
        elif '-ERRORX' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorx = pyaccel.lattice.get_error_misalignment_x(self._accelerator, idx[0])
            if value != prev_errorx:
                pyaccel.lattice.set_error_misalignment_x(self._accelerator, idx, value)
                self._state_deprecated = True
        elif '-ERRORY' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorx = pyaccel.lattice.get_error_misalignment_y(self._accelerator, idx[0])
            if value != prev_errorx:
                pyaccel.lattice.set_error_misalignment_y(self._accelerator, idx, value)
                self._state_deprecated = True

    def set_pv_quadrupoles(self, pv_name, value):
        if 'PS-Q' in pv_name:
            idx = self._get_elements_indices(pv_name)
            idx2 = idx
            while not isinstance(idx2,int):
                idx2 = idx2[0]
            prev_value = self._accelerator[idx2].polynom_b[1]
            if value != prev_quad_value:
                if isinstance(idx,int): idx = [idx]
                for i in idx:
                    self._accelerator[i].polynom_b[1] = value
                self._state_deprecated = True
            return True
        return False # [pv is not a quadrupole]

    def set_pv_correctors(self, pv_name, value):
        if 'PS-CH' in pv_name:
            idx = self._get_elements_indices(pv_name)
            nr_segs = len(idx)
            kickfield = 'hkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'hkick_polynom'
            prev_value = nr_segs * getattr(self._accelerator[idx[0]], kickfield)
            if value != prev_value:
                pyaccel.lattice.setattributelat(self._accelerator, kickfield, idx, value/nr_segs)
                self._state_deprecated = True
            return True

        if 'PS-CV' in pv_name:
            idx = self._get_elements_indices(pv_name)
            nr_segs = len(idx)
            kickfield = 'vkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'vkick_polynom'
            prev_value = nr_segs * getattr(self._accelerator[idx[0]], kickfield)
            if value != prev_value:
                pyaccel.lattice.setattributelat(self._accelerator, kickfield, idx, value/nr_segs)
                self._state_deprecated = True
            return True
        return False  # [pv is not a corrector]

    def set_pv_bends(self, pv_name, value):
        if 'PS-BEND-' in pv_name or 'PU-SEP' in pv_name:
            idx = self._get_elements_indices(pv_name)
            prev_value = 0
            for i in idx:
                prev_value += self._accelerator[i].polynom_b[0]*self._accelerator[i].length
                prev_value += self._accelerator[i].angle
            if value != prev_value:
                for i in idx:
                    angle_i = self._accelerator[i].angle
                    new_angle_i = angle_i *(value/prev_value)
                    self._accelerator[i].polynom_b[0] = (new_angle_i - angle_i)/self._accelerator[i].length
                self._state_deprecated = True
            return True
        return False


class TimingModel(Model):

    def __init__(self, model_module, all_pvs=None, log_func=utils.log):

        super().__init__(model_module=model_module, all_pvs=None, log_func=log_func)
        self.reset('start')

    def reset(self, message1='reset', message2='', c='white', a=None):
        if self._all_pvs is None:
            self._record_names = self._model_module.record_names.get_record_names()
        else:
            self._record_names = self._all_pvs
        if not message2:
            message2 = self._model_module.lattice_version
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)

        self._cycle = 0
        self._bo_kickin_on = 1
        self._bo_kickin_delay = 0
        self._bo_kickex_on = 1
        self._bo_kickex_delay = 0
        self._bo_kickex_inc = 0
        self._si_kickin_on = 1
        self._si_kickin_delay = 0

    def signal_all_models_set(self):
        if self._driver:
            si_rfrequency = self._driver.si_model.get_pv('RF-FREQUENCY')
            self._bo_kickex_inc = 1.0 / si_rfrequency

    def _set_delay_next_cycle(self):
        self._bo_kickex_delay += self._bo_kickex_inc
        self._driver.setParam('TI-BO-KICKEX-DELAY', self._bo_kickex_delay)

    def _incoming_bunch_injected_in_si(self, charge):
            rffrequency = pyaccel.optics.getrffrequency(self._driver.si_model._accelerator)
            bunch_offset = round(self._bo_kickex_delay * rffrequency)
            harmonic_number = self._driver.si_model._accelerator.harmonic_number
            bunch_charge = [0.0] * harmonic_number
            for i in range(len(charge)):
                n = (i + bunch_offset) % harmonic_number
                bunch_charge[n] += charge[i]
            return bunch_charge

    def beam_inject(self):
        if not self._cycle: return

        self._log(message1 = 'cycle', message2 = 'TI starting injection')

        # create charge from electron gun
        if self._driver.li_model._single_bunch_mode:
            charge = [self._driver.li_model._model_module.single_bunch_charge]
        else:
            raise Exception('multi-bunch mode not implemented')
        self._log(message1 = 'cycle', message2 = 'electron gun providing ' + str(sum(charge)*1e9) + ' nC of charge', c='white')

        # transport through linac
        self._log(message1 = 'cycle', message2 = 'injection in LI, ' + str(sum(charge)*1e9) + ' nC of charge', c='white')
        charge = self._driver.li_model.beam_transport(charge)
        self._driver.li_model.notify_driver()
        self._log(message1 = 'cycle', message2 = 'ejection from LI, ' + str(sum(charge)*1e9) + ' nC of charge', c='white')

        # transport through linac-to-booster transport line
        self._log(message1 = 'cycle', message2 = 'injection in TB, ' + str(sum(charge)*1e9) + ' nC of charge', c='white')
        charge = self._driver.tb_model.beam_transport(charge)
        self._driver.tb_model.notify_driver()
        self._log(message1 = 'cycle', message2 = 'ejection from TB, ' + str(sum(charge)*1e9) + ' nC of charge', c='white')

        # injection into booster
        self._log(message1 = 'cycle', message2 = 'injection in BO, ' + str(sum(charge)*1e9) + ' nC of charge', c='white')
        if self._bo_kickin_on:
            charge = self._driver.bo_model.beam_inject(charge = charge, message1='cycle', message2 = 'injection into SI, ' + str(sum(charge)*1e9) + ' nC', c='white', a=None)
        else:
            charge = [0]

        # acceleration through booster
        self._log(message1 = 'cycle', message2 = 'acceleration through BO, ' + str(sum(charge)*1e9) + ' nC of charge', c='white')
        charge = self._driver.bo_model.beam_accelerate()
        # ejection from booster
        if self._bo_kickex_on:
            charge = self._driver.bo_model.beam_eject(message1='')
        else:
            charge = [0]
        self._log(message1 = 'cycle', message2 = 'ejection from BO, ' + str(sum(charge)*1e9) + ' nC of charge', c='white')
        self._driver.bo_model.notify_driver()

        # transport through booster-to-storage ring transport line
        self._log(message1 = 'cycle', message2 = 'injection in TS, ' + str(sum(charge)*1e9) + ' nC of charge', c='white')
        charge = self._driver.ts_model.beam_transport(charge)
        self._driver.ts_model.notify_driver()
        self._log(message1 = 'cycle', message2 = 'ejection from TS, ' + str(sum(charge)*1e9) + ' nC of charge', c='white')

        # inject at storage ring
        charge = self._incoming_bunch_injected_in_si(charge)
        self._driver.si_model.beam_inject(charge = charge, message1='cycle', message2 = 'injection into SI, ' + str(sum(charge)*1e9) + ' nC', c='white', a=None)
        self._driver.si_model.notify_driver()

        # prepares internal data for next cycle
        self._set_delay_next_cycle()

    def get_pv_static(self, pv_name):
        if 'CYCLE' in pv_name:
            return self._cycle
        elif 'BO-KICKIN-ON' in pv_name:
            return self._bo_kickin_on
        elif 'BO-KICKIN-DELAY' in pv_name:
            return self._bo_kickin_delay
        elif 'BO-KICKEX-ON' in pv_name:
            return self._bo_kickex_on
        elif 'BO-KICKEX-DELAY' in pv_name:
            return self._bo_kickex_delay
        elif 'BO-KICKEX-INC' in pv_name:
            return self._bo_kickex_inc
        elif 'SI-KICKIN-ON' in pv_name:
            return self._si_kickin_on
        elif 'SI-KICKIN-DELAY' in pv_name:
            return self._si_kickin_delay
        elif 'SI-KICKIN-INC' in pv_name:
            return self._si_kickin_inc
        # elif 'TI-DELAY-BO2SI-DELTA' in pv_name:
        #     if self._delay_bo2si_delta is None:
        #         rfrequency = self._driver.si_model.get_pv('SIRF-FREQUENCY')
        #         self._delay_bo2si_delta = 1.0 / rfrequency
        #     return self._delay_bo2si_delta
        # elif 'TI-DELAY-BO2SI-INC' in pv_name:
        #     self._delay_bo2si_inc = 0
        #     return self._delay_bo2si_inc
        # elif 'TI-DELAY-BO2SI' in pv_name:
        #     return self._delay_bo2si
        else:
            return None

    def set_pv(self, pv_name, value):
        if 'CYCLE' in pv_name:
            self._cycle = value
            self.beam_inject()
            self._cycle = 0
            self._driver.setParam(pv_name, self._cycle)
        elif 'BO-KICKIN-ON' in pv_name:
            self._bo_kickin_on = value
        elif 'BO-KICKIN-DELAY' in pv_name:
            self._bo_kickin_delay = value
        elif 'BO-KICKEX-ON' in pv_name:
            self._bo_kickex_on = value
        elif 'BO-KICKEX-DELAY' in pv_name:
            self._bo_kickex_delay = value
        elif 'SI-KICKIN-ON' in pv_name:
            self._si_kickin_on = value
        elif 'SI-KICKIN-DELAY' in pv_name:
            self._si_kickin_delay = value
        elif 'SI-KICKIN-INC' in pv_name:
            self._si_kickin_inc = value
        # elif 'DELAY-BO2SI-DELTA' in pv_name:
        #     self._delay_bo2si_delta = value
        # elif 'DELAY-BO2SI-INC' in pv_name:
        #     if value:
        #         self._set_delay_bo2si_inc(value)
        # elif 'DELAY-BO2SI' in pv_name:
        #     self._delay_bo2si = value
        return None


#--- sirius-specific model classes ---#

class LiModel(TLineModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.li, all_pvs=all_pvs, log_func=log_func)
        self._single_bunch_mode   = True
        self._pulse_duration      = sirius.li.pulse_duration_interval[1]

        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.li_changed = True


class TbModel(TLineModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.tb, all_pvs=all_pvs, log_func=log_func)
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=sirius.bo.harmonic_number)
        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.tb_changed = True

    def get_init_twiss(self):
        return sirius.tb.initial_twiss

class TsModel(TLineModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.ts, all_pvs=all_pvs, log_func=log_func)
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=sirius.bo.harmonic_number)
        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.ts_changed = True

    def get_init_twiss(self):
        idx = pyaccel.lattice.findcells(self._driver.bo_model._accelerator, 'fam_name', 'sept_ex')
        twiss_at_boseptex = self._driver.bo_model._twiss[idx[0]]
        return twiss_at_boseptex

class SiModel(RingModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.si, all_pvs=all_pvs, log_func=log_func)
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(nr_bunches=self._accelerator.harmonic_number)
        self._init_families_str()
        self._calc_lifetimes()

    def notify_driver(self):
        if self._driver: self._driver.si_changed = True


class BoModel(RingModel):

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(sirius.bo, all_pvs=all_pvs, log_func=log_func)
        #self._accelerator.energy = 0.15e9 # [eV]
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER

        self._beam_charge = utils.BeamCharge(nr_bunches=self._accelerator.harmonic_number)
        #self._beam_charge.inject(0.0) # [coulomb]
        self._init_families_str()
        self._calc_lifetimes()

    def notify_driver(self):
        if self._driver: self._driver.bo_changed = True


class TiModel(TimingModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.ti, all_pvs=all_pvs, log_func=log_func)
        # if self._delay_bo2si_delta is None:
        #     rfrequency = self._driver.si_model.get_pv('SIRF-FREQUENCY')
        #     self._delay_bo2si_delta = 1.0 / rfrequency
        self._state_deprecated = True
        self.notify_driver()

    def notify_driver(self):
        if self._driver: self._driver.ti_changed = True
