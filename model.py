
"""Accelerator model module

The Model class in this module is in charge of the initialisation and
interaction with the engine (pyaccel/trackcpp). It updates values and
recalculates necessary parameters, controlling concurrent accesses coming from
the server.
"""

import time
import queue
import pyaccel
import sirius
import utils

PROCESSING_INTERVAL = 0.05

class Model(object):

    def __init__(self, machine):

        self._is_processing = False
        self._queue = queue.Queue()
        self._machine = machine

        # stored model state parameters
        self._beam_energy = None
        self._accelerator = None
        self._beam_lifetime = 0.0 # [h]
        self._beam_current = None
        self._orbit = None
        self._tunes = None

        # state flags for various calculated parameters
        self._orbit_depricated = True
        self._linear_optics_depricated = True

    def get_pv(self, reason):
        if 'BPM' in reason:
            if self._orbit_depricated:
                self._calc_orbit()
            orbit = self._orbit[:, pv_names.bpm[reason[2:]]]
            return (orbit[0], orbit[2])
        elif 'TVHOUR' in reason:
            return self._beam_lifetime
        elif 'TVMIN' in reason:
            return 60.0 * self._beam_lifetime
        elif 'PA-CURRENT' in reason:
            current = self._beam_current.value
            return current
        elif 'PA-TUNE' in reason:
            if self._linear_optics_depricated:
                self._calc_linear_optics()
                self._linear_optics_depricated = False
            if 'TUNEX' in reason:
                pass



    def set_pv(self, pv, value):
        self._queue.put((pv, value))
        return True

    def process(self):
        if self._is_processing:
            return

        print('starting processing loop')
        self._is_processing = True
        while(self._is_processing):
            while not self._queue.empty():
                value = self._queue.get()
            time.sleep(PROCESSING_INTERVAL)
        print('stopping processing loop')

    def stop(self):
        self._is_processing = False

    def _calc_orbit(self):
        self._orbit = pyaccel.tracking.findorbit4(self._accelerator, indices='open')
        self._orbit_depricated = False

    def _calc_linear_optics(self):
        if self._orbit_depricated:
            self._calc_orbit()
        pyaccel.optics.calctwiss(self._accelerator, closed_orbit=self._closed_orbit)


class SiModel(Model):

    def __init__(self):
        super().__init__(sirius.si)
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
