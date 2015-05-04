
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

TRACK6D = False

class Model(object):

    def __init__(self, machine, update_callback):

        self._machine = machine
        self._update_callback = update_callback
        self._is_processing = False

        # stored model state parameters
        self._record_names  = sirius.si.record_names.get_record_names
        self._accelerator   = None
        self._beam_lifetime = 0.0 # [h]
        self._beam_current  = None
        self._orbit = None
        self._tunes = [0.0, 0.0, 0.0]

        # state flags for various calculated parameters
        self._orbit_deprecated = True
        self._linear_optics_deprecated = True

    def beam_lost(self):
        self._beam_current.dump()
        self._cloed_orbit = numpy.zeros((6,len(self._accelerator)))
        self._tunes = [0.0, 0.0, 0.0]

    def get_pv(self, pv_name):

        # process global parameters
        if 'TVHOUR' in pv_name:
            return self._beam_lifetime
        elif 'TVMIN' in pv_name:
            return 60.0 * self._beam_lifetime
        elif 'PA-CURRENT' in pv_name:
            current = self._beam_current.value
            return current
        elif '-BPM-' in pv_name:
            bpm_idx = self._record_names[pv_name]['bpm'][0]
            orbit = 1000 * self._closed_orbit[[0,2],bpm_idx]   # [mm]
            return orbit
        elif 'PA-TUNEH' in pv_name:
            return self._tunes[0]
        elif 'PA-TUNEV' in pv_name:
            return self._tunes[1]
        else:
            return float("nan")

    def set_pv(self, pv_name, value):
        if 'PS-CHS-' in pv_name:
            chs_idx = self._record_names[pv_name]['chs'][0]
            prev_value = self._accelerator[chs_idx].hkick_polynom
            if prev_value == value:
                return
            self._accelerator[chs_idx].hkick_polynom = value
            self._orbit_deprecated = True
            self._linear_optics_deprecated = True
        if 'PS-CVS-' in pv_name:
            cvs_idx = self._record_names[pv_name]['cvs'][0]
            self._accelerator[cvs_idx].vkick_polynom = value
            self._orbit_deprecated = True
            self._linear_optics_deprecated = True
        if 'PS-CHF-' in pv_name:
            chf_idx = self._record_names[pv_name]['chf'][0]
            self._accelerator[chf_idx].hkick_polynom = value
            self._orbit_deprecated = True
            self._linear_optics_deprecated = True
        return True

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
            self.beam_lost()
        self._orbit_deprecated = False

    def _calc_linear_optics(self):
        if self._orbit_deprecated:
            self._calc_closed_orbit()
        tw, *_ = pyaccel.optics.calctwiss(self._accelerator, closed_orbit=self._closed_orbit)
        mux, muy = pyaccel.optics.gettwiss(tw,('mux','muy'))
        self._tunes[0] = mux[-1]/2/math.pi
        self._tunes[1] = muy[-1]/2/math.pi
        self._linear_optics_deprecated = False


class SiModel(Model):

    def __init__(self, update_callback=None):
        super().__init__(sirius.si, update_callback)
        self._record_names = sirius.si.record_names.get_record_names()
        self._accelerator = self._machine.create_accelerator()
        self._accelerator.energy = 3e9 # [eV]
        self._accelerator.cavity_on = TRACK6D
        self._accelerator.radiation_on = TRACK6D
        self._accelerator.vchamber_on = False
        self._beam_lifetime = 10.0 # [h]
        self._beam_current = utils.BeamCurrent(lifetime=self._beam_lifetime)
        self._beam_current.inject(300)   # [mA]

        #self._accelerator[10].hkick_polynom = 1.0e-4
