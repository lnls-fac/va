
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
        self._is_processing = False
        self._accelerator = machine.create_accelerator()
        self._queue = queue.Queue()

    def get_pv(self, pv):
        # Identify PV
        # Return PV value
        return 0.0

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
                print(value)
            time.sleep(PROCESSING_INTERVAL)
        print('stopping processing loop')

    def stop(self):
        self._is_processing = False


class SiModel(Model):

    def __init__(self):
        super().__init__(sirius.SI_V07)
