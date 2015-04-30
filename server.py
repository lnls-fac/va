#!/usr/bin/env python3

import time
import signal
import threading
from pcaspy import Driver, SimpleServer
import va.model as models
import va.si_pvs as si_pvs


WAIT_TIMEOUT = 0.2


class PCASDriver(Driver):

    def  __init__(self, si_model):
        super().__init__()
        self.si_model = si_model

    def read(self, reason):
        if reason.startswith('SI'):
            value = self.si_model.get_pv(reason)
        else:
            raise Exception('model not implemented')

        return value

    def write(self, reason, value):
        if reason.startswith('SI'):
            model = self.si_model
        else:
            raise Exception('model not implemented')

        model.set_pv(reason, value)


class DriverThread(threading.Thread):

    def __init__(self, driver, stop_event):
        self._driver = driver
        self._stop_event = stop_event
        super().__init__(target=self._main)

    def _main(self):
        while not self._stop_event.wait(WAIT_TIMEOUT):
            print('waiting...')
        else:
            print('exiting')


class ModelThread(threading.Thread):

    def __init__(self, model, stop_event=None):
        self._model = model
        self._stop_event = stop_event
        super().__init__(target=self._main)

    def stop(self):
        self._model.stop()
        self.join()
        return self.is_alive()

    def _main(self):
        self._model.process()


def handler(signum, frame):
    global si_thread
    print('Received signal', signum)
    print('Active thread count:', threading.active_count())
    print('Is alive?', si_thread.stop())

    global stop_event
    stop_event.set()


if __name__ == '__main__':

    stop_event = threading.Event()
    signal.signal(signal.SIGINT, handler)

    si = models.SiModel()

    si_thread = ModelThread(si)
    si_thread.start()

    pvdb = {}
    for key in pv_names.bpm.keys():
        pvdb['SI'+key] = {
            'type': 'float',
            'count': 2,
            'scan': 0.1,
        }

    server = SimpleServer()
    server.createPV('', si_pvs.database)
    driver = PCASDriver(si)

    # driver_thread = DriverThread(driver, stop_event)
    # driver_thread.start()

    is_running = True
    while True:
        server.process(0.1)
