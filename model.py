
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


TRACK6D = False
VCHAMBER = False
UNDEF_VALUE = 0.0 #float('nan')
_u, _Tp = mathphys.units, pyaccel.optics.getrevolutionperiod

class Model(object):

    def __init__(self, model_module, log_func=utils.log):

        # stored model state parameters
        self._model_module = model_module
        self._log = log_func
        self.reset('start')

    def reset_state_flags(self):
        # state flags for various calculated parameters
        self._orbit_deprecated = True
        self._linear_optics_deprecated = True
        self._equilibrium_deprecated = True

    def reset(self, message1='reset', message2='', c='white', a=None):
        self._record_names = self._model_module.record_names.get_record_names()
        self._accelerator = self._model_module.create_accelerator()
        self._beam_charge  = utils.BeamCharge()
        self._quad_families_str = {}
        self._sext_families_str = {}
        self.beam_init(message1,message2,c,a)

    def beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        self._beam_charge.dump()
        self._closed_orbit = None
        self._twiss = None
        self._m66 = None
        self._transfer_matrices = None
        self._summary = None

    def beam_init(self, message1='init', message2=None, c='white', a=None):
        if not message2:
            message2 = self._model_module.lattice_version
        self.beam_dump(message1,message2,c,a)
        self.reset_state_flags()

    def beam_inject(self, charge, message1='inject', message2 = '', c='white', a=None):
        if message1:
            self._log(message1, message2, c=c, a=a)
        if not self._beam_charge.total_value:
            self.reset_state_flags()
        self._beam_charge.inject(charge)

    def _get_elements_indices_correctors(self, pv_name):
        """Get index of model element which corresponds to single-element PV"""
        data = self._record_names[pv_name]
        idx = []
        keys = list(data.keys())
        idx = data[keys[0]]
        return idx

    def _get_elements_indices(self, pv_name):
        """Get flattened indices of element in the model"""
        data = self._record_names[pv_name]
        indices = []
        for key in data.keys():
            idx = lnls.utils.flatten(data[key])
            indices.extend(idx)
        return indices

    def get_pv(self, pv_name):

        value = self.get_pv_dynamic(pv_name)
        if value is None:
            value = self.get_pv_static(pv_name)
        if value is None:
            value = self.get_pv_fake(pv_name)
        if value is None:
            raise Exception('response to ' + pv_name + ' not implemented in model get_pv')
        return value

    def get_pv_fake(self, pv_name):
        if 'FK-' in pv_name:
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
        else:
            return None

    def get_pv_static(self, pv_name):
        # process global parameters
        if 'PA-LIFETIME' in pv_name:
            return self._beam_charge.average_lifetime / _u.hour
        elif 'PA-BLIFETIME' in pv_name:
            lifetime_hour = [bunch_lifetime / _u.hour for bunch_lifetime in self._beam_charge.lifetime]
            return lifetime_hour
        elif '-BPM-' in pv_name:
            idx = self._get_elements_indices(pv_name)
            if 'FAM-X' in pv_name:
                try:
                    pos_x = self._closed_orbit[0,idx]
                except TypeError:
                    pos_x = [UNDEF_VALUE]*180
                return pos_x
            elif 'FAM-Y' in pv_name:
                try:
                    pos_y = self._closed_orbit[2,idx]
                except TypeError:
                    pos_y = [UNDEF_VALUE]*180
                return pos_y
            else:
                try:
                    pos = self._closed_orbit[[0,2],idx[0]]
                except TypeError:
                    pos = UNDEF_VALUE, UNDEF_VALUE
                return pos
        elif 'DI-TUNEH' in pv_name:
            try:
                tune_value = self._twiss[-1].mux / 2.0 / math.pi
            except TypeError:
                tune_value = UNDEF_VALUE
            return tune_value
        elif 'DI-TUNEV' in pv_name:
            try:
                tune_value = self._twiss[-1].muy / 2.0 / math.pi
            except TypeError:
                tune_value = UNDEF_VALUE
            return tune_value
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
                pv_fam = '-'.join(pv_name.split()[:-1]) + '-FAM'
                try:
                    family_value = self._quad_families_str[pv_fam]
                except:
                    family_value = 0.0
                value = self._accelerator[idx[0]].polynom_b[1] - family_value
                return value
        elif 'PS-S' in pv_name:
            if '-FAM' in pv_name:
                value = self._sext_families_str[pv_name]
                return value
            else:
                idx = self._get_elements_indices(pv_name)
                pv_fam = '-'.join(pv_name.split()[:-1]) + '-FAM'
                try:
                    family_value = self._sext_families_str[pv_fam]
                except:
                    family_value = 0.0
                value = self._accelerator[idx[0]].polynom_b[2] - family_value
                return value
        elif 'PS-BEND' in pv_name:
            return self._accelerator.energy
        elif 'PS-QS' in pv_name:
            idx = self._get_element_index(pv_name)
            while not isinstance(idx, int): idx = idx[0]
            value = self._accelerator[idx].polynom_a[1]
            return value
        elif 'PA-CHROMX':
            return UNDEF_VALUE
        elif 'PA-CHROMY':
            return UNDEF_VALUE
        else:
            return None

    def set_pv(self, pv_name, value):
        if self.set_pv_correctors(pv_name, value): return
        if self.set_pv_quadrupoles_skew(pv_name, value): return  # has to be before quadrupoles
        if self.set_pv_quadrupoles(pv_name, value): return
        if self.set_pv_sextupoles(pv_name, value): return


        if 'FK-RESET' in pv_name:
            self.reset(message1='reset',message2=self._model_module.lattice_version)
        if 'FK-INJECT' in pv_name:
            charge = value * _u.mA * _Tp(self._accelerator)
            self.beam_inject(charge, message1='inject', message2 = str(value)+' mA', c='green')
        elif 'FK-DUMP' in pv_name:
            self.beam_dump(message1='dump',message2='beam at ' + self._model_module.lattice_version)

    def set_pv_quadrupoles_skew(self, pv_name, value):
        if 'PS-Q' in pv_name:
            indices = self._get_elements_indices_correctors(pv_name)
            prev_Ks = pyaccel.lattice.getattributelat(self._accelerator, 'polynom_a', indices, m=1)
            if value != prev_Ks[0]:
                for idx in indices:
                    self._accelerator[idx].polynom_a[1] = value
                self._orbit_deprecated = True
                self._linear_optics_deprecated = True
                self._equilibrium_deprecated = True
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
                    self._orbit_deprecated = True
                    self._linear_optics_deprecated = True
                    self._equilibrium_deprecated = True
            else:
                # individual sext PV
                idx = self._get_element_index(pv_name)
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
                    self._orbit_deprecated = True
                    self._linear_optics_deprecated = True
                    self._equilibrium_deprecated = True
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
                    self._orbit_deprecated = True
                    self._linear_optics_deprecated = True
                    self._equilibrium_deprecated = True
            else:
                # individual quad PV
                idx = self._get_element_index(pv_name)
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
                    self._orbit_deprecated = True
                    self._linear_optics_deprecated = True
                    self._equilibrium_deprecated = True

            return True

        return False # [pv is not a quadrupole]

    def set_pv_correctors(self, pv_name, value):

        if 'PS-CH' in pv_name:
            idx = self._get_elements_indices_correctors(pv_name)
            nr_segs = len(idx)
            kickfield = 'hkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'hkick_polynom'
            prev_value = nr_segs * getattr(self._accelerator[idx[0]], kickfield)
            if value != prev_value:
                pyaccel.lattice.setattributelat(self._accelerator, kickfield, idx, value/nr_segs)
                self._orbit_deprecated = True
                self._linear_optics_deprecated = True
                self._equilibrium_deprecated = True
            return True

        if 'PS-CV' in pv_name:
            idx = self._get_elements_indices_correctors(pv_name)
            nr_segs = len(idx)
            kickfield = 'vkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'vkick_polynom'
            prev_value = nr_segs * getattr(self._accelerator[idx[0]], kickfield)
            if value != prev_value:
                pyaccel.lattice.setattributelat(self._accelerator, kickfield, idx, value/nr_segs)
                self._orbit_deprecated = True
                self._linear_optics_deprecated = True
                self._equilibrium_deprecated = True
            return True

        return False  # [pv is not a corrector]

    def update_state(self):

        if self._orbit_deprecated:
            self._calc_closed_orbit()
        if self._linear_optics_deprecated:
            self._calc_linear_optics()
        if self._equilibrium_deprecated:
            self._calc_equilibrium_parameters()

    def _calc_closed_orbit(self):

        if self._beam_charge.total_value:
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
        self._orbit_deprecated = False

    def _calc_linear_optics(self):

        if self._beam_charge.total_value:
            # calcs linear optics when there is beam
            if self._orbit_deprecated:
                self._calc_closed_orbit()
            try:
                # optics
                self._log('calc', 'linear optics for '+self._model_module.lattice_version)
                self._twiss, self._m66, self._transfer_matrices, self._closed_orbit = \
                  pyaccel.optics.calctwiss(accelerator=self._accelerator,
                                           closed_orbit=self._closed_orbit)
            except numpy.linalg.linalg.LinAlgError:
                # beam is lost
                self.beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')
            except pyaccel.optics.OpticsException:
                # beam is lost
                self.beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')
            except pyaccel.tracking.TrackingException:
                # beam is lost
                self.beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')

        self._linear_optics_deprecated = False

    def _calc_equilibrium_parameters(self):

        if self._beam_charge.total_value:
            if self._linear_optics_deprecated:
                self._calc_linear_optics(self)
            try:
                self._log('calc', 'equilibrium parameters for '+self._model_module.lattice_version)
                self._summary = pyaccel.optics.getequilibriumparameters(\
                                             accelerator=self._accelerator,
                                             twiss=self._twiss,
                                             m66=self._m66,
                                             transfer_matrices=self._transfer_matrices,
                                             closed_orbit=self._closed_orbit)
            except:
                raise Exception('problem')

        self._equilibrium_deprecated = False


    def _init_families_str(self):
        rnames = self._record_names
        for pv_name in rnames.keys():
            #print(pv_name)
            if '-FAM' in pv_name:
                if 'PS-Q' in pv_name:
                    idx = self._get_elements_indices(pv_name)
                    value = self._accelerator[idx[0]].polynom_b[1]
                    self._quad_families_str[pv_name] = value
                if 'PS-S' in pv_name:
                    idx = self._get_elements_indices(pv_name)
                    value = self._accelerator[idx[0]].polynom_b[2]
                    self._sext_families_str[pv_name] = value


class SiModel(Model):

    def __init__(self, log_func=utils.log):

        super().__init__(sirius.si, log_func=log_func)
        #self._accelerator.energy = 3e9 # [eV]
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(lifetime=[10.0*_u.hour] * self._accelerator.harmonic_number)
        self._beam_charge.inject(300 * _u.mA * _Tp(self._accelerator)) # [coulomb]
        self._init_families_str()


class BoModel(Model):

    def __init__(self, log_func=utils.log):
        super().__init__(sirius.bo, log_func=log_func)
        #self._accelerator.energy = 0.15e9 # [eV]
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(lifetime=[1.0*_u.hour] * self._accelerator.harmonic_number)
        self._beam_charge.inject(2.0 * _u.mA * _Tp(self._accelerator)) # [coulomb]
        self._init_families_str()
