
"""Accelerator model module

The Model class in this module is in charge of the initialisation and
interaction with the engine (pyaccel/trackcpp). It updates values and
recalculates necessary parameters, controlling concurrent accesses coming from
the server.
"""

import time
import pyaccel
import sirius
import utils
import numpy
import math
import lnls.utils
import datetime


TRACK6D = False
UNDEF_VALUE = float('nan')

class Model(object):

    def __init__(self, model_module):

        # stored model state parameters
        self._model_module  = model_module
        self._record_names  = self._model_module.record_names.get_record_names()
        self._accelerator   = None
        self._beam_current  = utils.BeamCurrent()
        self._quad_families_str = {}
        self._sext_families_str = {}

        self.beam_init() # inits beam data structure

        # state flags for various calculated parameters
        self._orbit_deprecated = True
        self._linear_optics_deprecated = True

    def beam_init(self):
        self.beam_lost('init beam')

    def beam_lost(self, message='', c1='yellow', a1=None, c2='white', a2=None):
        self._beam_current.dump()
        self._closed_orbit = None
        self._twiss = None
        self._m66 = None
        self._transfer_matrices = None
        if message:
            print(utils.timestamp_message(message, c1=c1, a1=a1, c2=c2, a2=a2))

    def _get_element_index(self, pv_name):
        """Get index of model element which corresponds to single-element PV"""
        data = self._record_names[pv_name]
        keys = list(data.keys())
        idx = data[keys[0]]
        return idx

    def get_pv(self, pv_name):

        # process global parameters
        if 'TVHOUR' in pv_name:
            return self._beam_lifetime
        elif 'TVMIN' in pv_name:
            return 60.0 * self._beam_lifetime
        elif 'DI-CURRENT' in pv_name:
            current = self._beam_current.value
            return current
        elif '-BPM-' in pv_name:
            idx = self._get_element_index(pv_name)
            try:
                pos = self._closed_orbit[[0,2],idx[0]]
            except TypeError:
                pos = UNDEF_VALUE, UNDEF_VALUE
            return pos
        elif 'DI-TUNEH' in pv_name:
            try:
                tune_value = self._twiss[-1].mux / 2.0 / math.pi
            except TypeError:
                print(self._linear_optics_deprecated)
                tune_value = UNDEF_VALUE
            return tune_value
        elif 'DI-TUNEV' in pv_name:
            try:
                tune_value = self._twiss[-1].muy / 2.0 / math.pi
            except TypeError:
                tune_value = UNDEF_VALUE
            return tune_value
        elif 'PS-CH' in pv_name:
            idx = self._get_element_index(pv_name)
            kicks = pyaccel.lattice.getattributelat(self._accelerator, 'hkick_polynom', idx)
            value = sum(kicks)
            return value
        elif 'PS-CV' in pv_name:
            idx = self._get_element_index(pv_name)
            kicks = pyaccel.lattice.getattributelat(self._accelerator, 'vkick_polynom', idx)
            value = sum(kicks)
            return value
        elif 'PS-Q' in pv_name:
            if '-FAM' in pv_name:
                value = self._quad_families_str[pv_name]
                return value
            else:
                idx = self._get_element_index(pv_name)
                while not isinstance(idx, int): idx = idx[0]
                pv_fam = '-'.join(pv_name.split()[:-1]) + '-FAM'
                try:
                    family_value = self._quad_families_str[pv_fam]
                except:
                    family_value = 0.0
                value = self._accelerator[idx].polynom_b[1] - family_value
                return value
        elif 'PS-S' in pv_name:
            if '-FAM' in pv_name:
                value = self._sext_families_str[pv_name]
                return value
            else:
                idx = self._get_element_index(pv_name)
                while not isinstance(idx, int): idx = idx[0]
                pv_fam = '-'.join(pv_name.split()[:-1]) + '-FAM'
                try:
                    family_value = self._sext_families_str[pv_fam]
                except:
                    family_value = 0.0
                value = self._accelerator[idx].polynom_b[2] - family_value
                return value
        else:
            return float("nan")

    def set_pv(self, pv_name, value):
        if self.set_pv_correctors(pv_name, value): return
        if self.set_pv_quadrupoles(pv_name, value): return
        if self.set_pv_sextupoles(pv_name, value): return

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

            return True

        return False # [pv is not a quadrupole]

    def set_pv_correctors(self, pv_name, value):

        if 'PS-CH' in pv_name:
            idx = self._get_element_index(pv_name)
            nr_segs = len(idx)
            prev_value = nr_segs * self._accelerator[idx[0]].hkick_polynom
            if value != prev_value:
                pyaccel.lattice.setattributelat(self._accelerator, 'hkick_polynom', idx, value/nr_segs)
                self._orbit_deprecated = True
                self._linear_optics_deprecated = True
            return True

        if 'PS-CV' in pv_name:
            idx = self._get_element_index(pv_name)
            nr_segs = len(idx)
            prev_value = nr_segs * self._accelerator[idx[0]].vkick_polynom
            if value != prev_value:
                pyaccel.lattice.setattributelat(self._accelerator, 'vkick_polynom', idx, value/nr_segs)
                self._orbit_deprecated = True
                self._linear_optics_deprecated = True
            return True

        return False  # [pv is not a corrector]

    def update_state(self):
        if self._orbit_deprecated:
            self._calc_closed_orbit()
        if self._linear_optics_deprecated:
            self._calc_linear_optics()

    def _calc_closed_orbit(self):
        try:
            if TRACK6D:
                self._closed_orbit = pyaccel.tracking.findorbit6(self._accelerator, indices='open')
            else:
                self._closed_orbit = numpy.zeros((6,len(self._accelerator)))
                self._closed_orbit[:4,:] = pyaccel.tracking.findorbit4(self._accelerator, indices='open')
        except pyaccel.tracking.TrackingException:
            # beam is lost
            self.beam_lost('beam lost: no closed orbit found', c2='red')
        self._orbit_deprecated = False

    def _calc_linear_optics(self):

        if self._orbit_deprecated:
            self._calc_closed_orbit()
        try:

            # optics
            self._twiss, self._m66, self._transfer_matrices, self._closed_orbit = \
              pyaccel.optics.calctwiss(accelerator=self._accelerator,
                                       closed_orbit=self._closed_orbit)


        except numpy.linalg.linalg.LinAlgError:
            # beam is lost
            self.beam_lost('beam lost: unstable linear optics', c2='red')
        except pyaccel.optics.OpticsException:
            # beam is lost
            self.beam_lost('beam lost: unstable linear optics', c2='red')

        self._linear_optics_deprecated = False

    def _init_families_str(self):
        rnames = self._record_names
        for pv_name in rnames.keys():
            #print(pv_name)
            if '-FAM' in pv_name:
                if 'PS-Q' in pv_name:
                    idx = self._get_element_index(pv_name)
                    while not isinstance(idx,int): idx = idx[0]
                    value = self._accelerator[idx].polynom_b[1]
                    self._quad_families_str[pv_name] = value
                if 'PS-S' in pv_name:
                    idx = self._get_element_index(pv_name)
                    while not isinstance(idx,int): idx = idx[0]
                    value = self._accelerator[idx].polynom_b[2]
                    self._sext_families_str[pv_name] = value


class SiModel(Model):

    def __init__(self):

        super().__init__(sirius.si)
        self._record_names = sirius.si.record_names.get_record_names()
        self._accelerator = sirius.si.create_accelerator()
        self._accelerator.energy = 3e9 # [eV]
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = False
        self._beam_lifetime = 10.0 # [h]
        self._beam_current = utils.BeamCurrent(lifetime=self._beam_lifetime)
        self._beam_current.inject(300)   # [mA]
        self._init_families_str()




class BoModel(Model):

    def __init__(self):
        super().__init__(sirius.bo)
        self._record_names = sirius.bo.record_names.get_record_names()
        self._accelerator = self._model_module.create_accelerator()
        self._accelerator.energy = 0.15e9 # [eV]
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = False
        self._beam_lifetime = 1.0 # [h]
        self._beam_current = utils.BeamCurrent(lifetime=self._beam_lifetime)
        self._beam_current.inject(2)   # [mA]

        self._init_families_str()
