#!/usr/bin/env python3

import sys
import time
import signal
import queue
import threading
from pcaspy import Driver, SimpleServer
import va.model as models
import va.si_pvs as si_pvs


WAIT_TIMEOUT = 0.1


class PCASDriver(Driver):

    def  __init__(self, si_model):
        super().__init__()
        self.si_model = si_model
        self.queue = queue.Queue()

    def write(self, reason, value):
        self.queue.put((reason, value))
        self.setParam(reason, value)

    def update_pvs(self):
        for i in range(self.queue.qsize()):
            pv_name, value = self.queue.get()
            self.set_model_parameters(pv_name, value)
        self.update_model_state()
        self.update_pv_values()
        self.updatePVs()

    def set_model_parameters(self, pv_name, value):
        name, value = self.conv_hw2phys(pv_name, value)

        if pv_name.startswith('SI'):
            self.si_model.set_pv(name, value)
        elif pv_name.startswith('BO'):
            pass
        else:
            raise Exception('subsystem not found')

    def conv_hw2phys(self, pv_name, value):
        if pv_name.endswith('-SP'):
            name = pv_name[:-2]
        else:
            name = pv_name

        return name, value

    def update_model_state(self):
        self.si_model.update_state()

    def update_pv_values(self):
        for pv in si_pvs.read_only_pvs:
            self.setParam(pv, self.si_model.get_pv(pv))


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

        # print('exiting')


def handle_signal(signum, frame):
    global stop_event, driver_thread
    print('Received signal', signum)
    print('Active thread count:', threading.active_count())
    stop_event.set()
    driver_thread.join()


if __name__ == '__main__':

    if len(sys.argv) > 1:
        prefix = sys.argv[1]
    else:
        prefix = ''

    print('Using prefix "' + prefix + '".')

    si = models.SiModel()
    stop_event = threading.Event()

    server = SimpleServer()
    server.createPV(prefix, si_pvs.database)

    driver = PCASDriver(si)
    driver_thread = DriverThread(driver, stop_event)
    driver_thread.start()

    signal.signal(signal.SIGINT, handle_signal)

    while not stop_event.is_set():
        server.process(0.1)
