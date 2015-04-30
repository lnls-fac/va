
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

PROCESSING_INTERVAL = 0.05

class Model(object):

    def __init__(self, machine, update_callback):

        self._machine = machine
        self._update_callback = update_callback
        self._is_processing = False

        # stored model state parameters
        self._pvs = None
        self._beam_energy = None
        self._accelerator = None
        self._beam_lifetime = 0.0 # [h]
        self._beam_current = None
        self._orbit = None
        self._tunes = None

        # state flags for various calculated parameters
        self._orbit_deprecated = True
        self._linear_optics_deprecated = True

    def get_pv(self, pv_name):

        # process global parameters
        if 'TVHOUR' in pv_name:
            return self._beam_lifetime
        elif 'TVMIN' in pv_name:
            return 60.0 * self._beam_lifetime
        elif 'PA-CURRENT' in reason:
            current = self._beam_current.value
            return current
        elif 'PA-TUNE' in pv_name:
            if self._linear_optics_deprecated:
                self._calc_linear_optics()
                self._linear_optics_deprecated = False
            if 'TUNEX' in reason:
                pass



    def set_pv(self, pv_name, value):
        return True

    def _calc_orbit(self):
        self._orbit = pyaccel.tracking.findorbit4(self._accelerator, indices='open')
        self._orbit_deprecated = False

    def _calc_linear_optics(self):
        if self._orbit_deprecated:
            self._calc_orbit()
        pyaccel.optics.calctwiss(self._accelerator, closed_orbit=self._closed_orbit)


class SiModel(Model):

    def __init__(self, update_callback=None):
        super().__init__(sirius.si, update_callback)
        self._pvs = sirius.si.record_names.get_record_names()
        self._beam_energy = 3e9 # [eV]
        self._accelerator = self._machine.create_accelerator()
        self._accelerator.energy = self._beam_energy
        self._accelerator.cavity_on = True
        self._accelerator.radiation_on = True
        self._accelerator.vchamber_on = False
        self._beam_lifetime = 10.0 # [h]
        self._beam_current = utils.BeamCurrent(lifetime=self._beam_lifetime)
        self._beam_current.inject(300)   # [mA]

        self._accelerator[10].hkick_polynom = 1.0e-4
