
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
import va.si_pvs as si_pvs

PROCESSING_INTERVAL = 0.05

class Model(object):

    def __init__(self, machine, update_callback):

        self._machine = machine
        self._update_callback = update_callback
        self._queue = queue.Queue()
        self._is_processing = False

        # stored model state parameters
        self._beam_energy = None
        self._accelerator = None
        self._beam_lifetime = 0.0 # [h]
        self._beam_current = None
        self._orbit = None
        self._tunes = None

        # state flags for various calculated parameters
        self._orbit_deprecated = True
        self._linear_optics_deprecated = True

    def get_pv(self, reason):
        if 'BPM' in reason:
            if self._orbit_deprecated:
                self._calc_orbit()
            orbit = self._orbit[:, si_pvs.bpm[reason[2:]]]
            return (orbit[0], orbit[2])
        elif 'TVHOUR' in reason:
            return self._beam_lifetime
        elif 'TVMIN' in reason:
            return 60.0 * self._beam_lifetime
        elif 'PA-CURRENT' in reason:
            current = self._beam_current.value
            return current
        elif 'PA-TUNE' in reason:
            if self._linear_optics_deprecated:
                self._calc_linear_optics()
                self._linear_optics_deprecated = False
            if 'TUNEX' in reason:
                pass

    def set_pv(self, pv, value):
        self._queue.put((pv, value))
        return True

    def process(self, stop_event):
        if self._is_processing:
            return

        print('starting processing loop')
        self._is_processing = True
        while True:
            while not self._queue.empty():
                value = self._queue.get()
                self._process_request(value)
            if stop_event.wait(PROCESSING_INTERVAL):
                break
        self._is_processing = False
        print('stopping processing loop')

    def _process_request(self, request):
        try:
            name, value = request
        except:
            return

        if 'PS' in name:
            self._accelerator[10].hkick_polynom = value
            self._orbit_deprecated = True
            self._calc_orbit()


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
