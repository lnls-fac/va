
"""Accelerator model module

The Model class in this module is in charge of the initialisation and
interaction with the engine (pyaccel/trackcpp). It updates values and
recalculates necessary parameters, controlling concurrent accesses coming from
the server.
"""

import time
import queue
import pyaccel
import sirius.SI_V07


PROCESSING_INTERVAL = 0.05


class Model(object):

    def __init__(self, machine):
        self._processing = False
        self._accelerator = machine.create_accelerator()
        self._queue = queue.Queue()
        # self._ao = machine.get_ao()

    # begin public API
    def get_pv(self, pv):
        # Identify PV
        # Return PV value
        pass

    def set_pv(self, pv, value):
        # Identify PV
        # Set PV value
        # Trigger dependent recalculation
        pass

    def process(self):
        self._processing = True
        while(self._processing):
            while not self._queue.empty():
                value = self._queue.get()
                if value == 'STOP':
                    self._processing = False
                pass # set PV
            time.sleep(PROCESSING_INTERVAL)
            print('hi')
    # end public API


class SiModel(Model):

    def __init__(self):
        super().__init__(sirius.SI_V07)
