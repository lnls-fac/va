#!/usr/bin/env python3

import time
import signal
import threading
from pcaspy import Driver, SimpleServer
import va.model as models
import va.si_pvs as si_pvs


WAIT_TIMEOUT = 0.05


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

    def update_pvs(self):
        pass
        # self.setParam('SIPA-CURRENT', self.si_model.get_pv('PA-CURRENT'))
        # self.updatePVs()
        # print('updating PVs...')


class DriverThread(threading.Thread):

    def __init__(self, driver, stop_event):
        self._driver = driver
        self._stop_event = stop_event
        super().__init__(target=self._main)

    def _main(self):
        while True:
            t0 = time.time()
            self._driver.update_pvs()
            delta = time.time() - t0
            if self._stop_event.wait(WAIT_TIMEOUT - delta):
                break

        print('exiting')


class ModelThread(threading.Thread):

    def __init__(self, model, stop_event):
        self._model = model
        self._stop_event = stop_event
        super().__init__(target=self._main)

    def _main(self):
        self._model.process(self._stop_event)


def handle_signal(signum, frame):
    global stop_event
    print('Received signal', signum)
    print('Active thread count:', threading.active_count())
    stop_event.set()


if __name__ == '__main__':

    si = models.SiModel()
    stop_event = threading.Event()

    si_thread = ModelThread(si, stop_event)
    si_thread.start()

    server = SimpleServer()
    server.createPV('', si_pvs.database)

    driver = PCASDriver(si)
    driver_thread = DriverThread(driver, stop_event)
    driver_thread.start()

    signal.signal(signal.SIGINT, handle_signal)

    while not stop_event.is_set():
        server.process(0.1)
