
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
import va.pv_names as pv_names


PROCESSING_INTERVAL = 0.05


class Model(object):

    def __init__(self, machine):
        self._is_processing = False
        self._accelerator = machine.create_accelerator()
        self._beam_current = utils.BeamCurrent(current=300, lifetime=10)
        self._accelerator[10].hkick_polynom = 1.0e-4
        self._queue = queue.Queue()

        self._accelerator[10].hkick_polynom = 1.0e-4
        self._orbit_depricated = True

    def get_pv(self, reason):
        if 'BPM' in reason:
            if self._orbit_depricated:
                self._calc_orbit()
                self._orbit_depricated = False
            orbit = self._orbit[:, pv_names.bpm[reason[2:]]]
            return (orbit[0], orbit[2])
        elif 'CURRENT' in reason:
            current = self._current.value
            return current

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


class SiModel(Model):

    def __init__(self):
        super().__init__(sirius.si)
