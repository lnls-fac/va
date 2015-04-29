
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
import va.pv_names as pv_names


PROCESSING_INTERVAL = 0.05


class Model(object):

    def __init__(self, machine):
        self._is_processing = False
        self._accelerator = machine.create_accelerator()
        self._accelerator[10].hkick_polynom = 1.0e-4
        self._queue = queue.Queue()

    def get_pv(self, reason):
        if 'BPM' in reason:
            self._calc_orbit()
            orbit = self._orbit[:, pv_names.bpm[reason[2:]]]
            return (orbit[0], orbit[2])

        # if pv == 'PS':
        #     return self.pvs[pv]
        # elif pv == 'BPM':
        #     return 10*self.pvs['PS'] + 0.1
        # Identify PV
        # Return PV value
        # return (0.0, 1.0)

    def set_pv(self, pv, value):
        # Validate input
        # Identify PV
        # Set PV value
        # Trigger dependent recalculation
        # pass
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

                # name, value = value
                # self.pvs[name] = value

                print(value)
            time.sleep(PROCESSING_INTERVAL)
        print('stopping processing loop')

    def stop(self):
        self._is_processing = False

    def _calc_orbit(self):
        self._orbit = pyaccel.tracking.findorbit4(self._accelerator, indices='open')


class SiModel(Model):

    def __init__(self):
        super().__init__(sirius.si)