
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

    def __init__(self, model_module=None, all_pvs=None, log_func=utils.log):

        # stored model state parameters
        self._driver = None # this will be set latter by Driver
        self._model_module = model_module
        self._log = log_func
        self._all_pvs = all_pvs

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
        self._beam_charge  = utils.BeamCharge()
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
        self._beam_charge.dump()
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

    def beam_eject(self, message1='eject', message2 = '', c='white', a=None):
        if message1:
            self._log(message1, message2, c=c, a=a)
        charge = self._beam_charge.total_value
        self._beam_charge.dump()
        return charge

    def beam_charge(self):
        self.update_state()
        return self._beam_charge.total_value

    def beam_accelerate(self, charge):
        self.beam_inject(charge, message1='')
        charge = self._beam_charge.total_value
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
            #print('ok get_pv fake ERRORX')
            return error
        if '-ERRORY' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            error = pyaccel.lattice.get_error_misalignment_y(self._accelerator, idx[0])
            #print('ok get_pv fake ERRORY')
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
            #print(self._beam_charge.total_value)
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
                if self._closed_orbit is None: return [UNDEF_VALUE]*len(idx)
                return self._closed_orbit[0,idx]
            elif 'FAM-Y' in pv_name:
                if self._closed_orbit is None: return [UNDEF_VALUE]*len(idx)
                return self._closed_orbit[2,idx]
            else:
                if self._closed_orbit is None: return UNDEF_VALUE
                return self._closed_orbit[[0,2],idx[0]]
        elif 'DI-TUNEH' in pv_name:
            if self._twiss is None: return UNDEF_VALUE
            tune_value = self._twiss[-1].mux / 2.0 / math.pi
            return tune_value
        elif 'DI-TUNEV' in pv_name:
            if self._twiss is None: return UNDEF_VALUE
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
            return 0
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
        if self.set_pv_fake(pv_name, value): return

    def set_pv_fake(self, pv_name, value):
        if 'FK-RESET' in pv_name:
            self.reset(message1='reset',message2=self._model_module.lattice_version)
        elif 'FK-INJECT' in pv_name:
            charge = value * _u.mA * _Tp(self._accelerator)
            self.beam_inject(charge, message1='inject', message2 = str(value)+' mA', c='green')
        elif 'FK-DUMP' in pv_name:
            self.beam_dump(message1='dump',message2='beam at ' + self._model_module.lattice_version)
        elif '-ERRORX' in pv_name:
            #print('ok set_pv fake ERRORX')
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorx = pyaccel.lattice.get_error_misalignment_x(self._accelerator, idx[0])
            if value != prev_errorx:
                pyaccel.lattice.set_error_misalignment_x(self._accelerator, idx, value)
        elif '-ERRORY' in pv_name:
            #print('ok set_pv fake ERRORX')
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorx = pyaccel.lattice.get_error_misalignment_y(self._accelerator, idx[0])
            if value != prev_errorx:
                pyaccel.lattice.set_error_misalignment_y(self._accelerator, idx, value)


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

    def _calc_equilibrium_parameters(self):
        if self._m66 is None: return
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
        if not message2:
            message2 = self._model_module.lattice_version
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)

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
        self.update_state()

    def beam_transport(self, charge):
        self.beam_inject(charge, message1='')
        charge = self._beam_charge.total_value
        self._beam_charge.dump()
        return charge

    def beam_charge(self):
        self.update_state()
        return self._beam_charge.total_value

    def _get_elements_indices(self, pv_name):
        """Get flattened indices of element in the model"""
        data = self._record_names[pv_name]
        indices = []
        for key in data.keys():
            idx = lnls.utils.flatten(data[key])
            indices.extend(idx)
        return indices

    def get_pv_fake(self, pv_name):
        if 'FK-' in pv_name:
            return 0.0
        else:
            return None

    def get_pv_dynamic(self, pv_name):
        if 'DI-CURRENT' in pv_name:
            # time_interval = pyaccel.optics.getrevolutionperiod(self._accelerator)
            # currents = self._beam_charge.current(time_interval)
            # currents_mA = [bunch_current / _u.mA for bunch_current in currents]
            # #print(self._beam_charge.total_value)
            # return sum(currents_mA)
            return 0
        else:
            return None

    def get_pv_static(self, pv_name):
        # process global parameters
        if '-BPM-' in pv_name:
            idx = self._get_elements_indices(pv_name)
            try:
                #pos = self._closed_orbit[[0,2],idx[0]]
                pos = [0,0]
            except TypeError:
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
        elif 'PS-BEND' in pv_name:
            return 0
        elif 'PU-SEP' in pv_name:
            return 0
        else:
            return None

    def set_pv(self, pv_name, value):
        if self.set_pv_correctors(pv_name, value): return
        if self.set_pv_quadrupoles(pv_name, value): return

        if 'FK-RESET' in pv_name:
            self.reset(message1='reset',message2=self._model_module.lattice_version)
        if 'FK-INJECT' in pv_name:
            charge = value * _u.mA * _Tp(self._accelerator)
            self.beam_inject(charge, message1='inject', message2 = str(value)+' mA', c='green')
        elif 'FK-DUMP' in pv_name:
            self.beam_dump(message1='dump',message2='beam at ' + self._model_module.lattice_version)

    def set_pv_quadrupoles(self, pv_name, value):
        if 'PS-Q' in pv_name:
            # individual quad PV
            idx = self._get_elements_indices(pv_name)
            idx2 = idx
            while not isinstance(idx2,int):
                idx2 = idx2[0]
            prev_value = self._accelerator[idx2].polynom_b[1]
            if value != prev_quad_value:
                if isinstance(idx,int): idx = [idx]
                for i in idx:
                    self._accelerator[i].polynom_b[1] = value
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
            return True

        if 'PS-CV' in pv_name:
            idx = self._get_elements_indices(pv_name)
            nr_segs = len(idx)
            kickfield = 'vkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'vkick_polynom'
            prev_value = nr_segs * getattr(self._accelerator[idx[0]], kickfield)
            if value != prev_value:
                pyaccel.lattice.setattributelat(self._accelerator, kickfield, idx, value/nr_segs)
            return True
        return False  # [pv is not a corrector]


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

    def get_pv_static(self, pv_name):
        if 'CYCLE' in pv_name:
            return self._cycle
        else:
            return None

    def beam_inject(self):
        if not self._cycle: return

        self._log(message1 = 'cycle', message2 = 'TI starting injection')

        # create charge from electron gun
        charge = self._driver.li_model._single_bunch_charge
        self._log(message1 = 'cycle', message2 = 'electron gun providing ' + str(charge*1e9) + ' nC of charge', c='white')

        # transport through linac
        self._log(message1 = 'cycle', message2 = 'injection in LI, ' + str(charge*1e9) + ' nC of charge', c='white')
        charge = self._driver.li_model.beam_transport(charge)
        self._driver.li_model.notify_driver()
        self._log(message1 = 'cycle', message2 = 'ejection from LI, ' + str(charge*1e9) + ' nC of charge', c='white')

        # acceleration through booster
        self._log(message1 = 'cycle', message2 = 'injection in BO, ' + str(charge*1e9) + ' nC of charge', c='white')
        self._driver.bo_model.beam_accelerate(charge)
        charge = self._driver.bo_model.beam_eject(message1='')
        self._driver.bo_model.notify_driver()
        self._log(message1 = 'cycle', message2 = 'ejection from BO, ' + str(charge*1e9) + ' nC of charge', c='white')

        # inject at storage ring
        self._driver.si_model.beam_inject(charge = charge, message1='cycle', message2 = 'injection into SI, ' + str(charge/1e-9) + ' nC', c='white', a=None)
        self._driver.si_model.notify_driver()

    def set_pv(self, pv_name, value):
        if 'CYCLE' in pv_name:
            self._cycle = value
            self.beam_inject()
            self._cycle = 0
            self._driver.setParam(pv_name, self._cycle)
        return None


class LiModel(TLineModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.li, all_pvs=all_pvs, log_func=log_func)
        self._single_bunch_charge = 1e-9    #[coulomb]

    def notify_driver(self):
        if self._driver: self._driver.li_deprecated = True


class TbModel(TLineModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.tb, all_pvs=all_pvs, log_func=log_func)

    def notify_driver(self):
        if self._driver: self._driver.tb_deprecated = True


class TsModel(TLineModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.ts, all_pvs=all_pvs, log_func=log_func)

    def notify_driver(self):
        if self._driver: self._driver.ts_deprecated = True

class SiModel(RingModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.si, all_pvs=all_pvs, log_func=log_func)
        #self._accelerator.energy = 3e9 # [eV]
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(lifetime=[10.0*_u.hour] * self._accelerator.harmonic_number)
        self._beam_charge.inject(0 * 300 * _u.mA * _Tp(self._accelerator)) # [coulomb]
        self._init_families_str()

    def notify_driver(self):
        if self._driver: self._driver.si_deprecated = True

class BoModel(RingModel):

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(sirius.bo, all_pvs=all_pvs, log_func=log_func)
        #self._accelerator.energy = 0.15e9 # [eV]
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = VCHAMBER
        self._beam_charge = utils.BeamCharge(lifetime=[1.0*_u.hour] * self._accelerator.harmonic_number)
        self._beam_charge.inject(0 * 2.0 * _u.mA * _Tp(self._accelerator)) # [coulomb]
        self._init_families_str()

    def notify_driver(self):
        if self._driver: self._driver.bo_deprecated = True


class TiModel(TimingModel):

    def __init__(self, all_pvs=None, log_func=utils.log):

        super().__init__(sirius.ti, all_pvs=all_pvs, log_func=log_func)

    def notify_driver(self):
        if self._driver: self._driver.ti_deprecated = True
