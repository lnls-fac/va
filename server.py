#!/usr/bin/env python3

import sys
import time
import signal
import queue
import threading
from pcaspy import Driver, SimpleServer
import va.model as models
import va.si_pvs as si_pvs
#import va.bo_pvs as bo_pvs
#import va.ts_pvs as ts_pvs
#import va.tb_pvs as tb_pvs
#import va.li_pvs as li_pvs


WAIT_TIMEOUT = 0.1


class PCASDriver(Driver):

    def  __init__(self, si_model = None,
                        bo_model = None,
                        ts_model = None,
                        tb_model = None,
                        li_model = None):
        super().__init__()
        self.si_model = si_model
        self.bo_model = bo_model
        self.ts_model = ts_model
        self.tb_model = tb_model
        self.li_model = li_model
        self.queue = queue.Queue()

    def read(self, reason):
        print('read:' + reason)
        return super().read(reason)

    def write(self, reason, value):
        print('write: ' + reason)
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
            raise Exception('BO model not implemented yet')
        elif pv_name.startswith('TS'):
            raise Exception('TS model not implemented yet')
        elif pv_name.startswith('TB'):
            raise Exception('TB model not implemented yet')
        elif pv_name.startswith('LI'):
            raise Exception('LI model not implemented yet')
        else:
            raise Exception('subsystem not found')

    def conv_hw2phys(self, pv_name, value):
        if pv_name.endswith('-SP'):
            name = pv_name[:-3]
        elif pv_name.endswith('-RB'):
            name = pv_name[:-3]
        else:
            name = pv_name

        return name, value

    def update_model_state(self):
        self.si_model.update_state()
        #self.bo_model.update_state()
        #self.ts_model.update_state()
        #self.tb_model.update_state()
        #self.li_model.update_state()

    def update_sp_pv_values(self):
        for pv in si_pvs.read_write_pvs:
            self.setParam(pv, self.si_model.get_pv(pv))

    def update_pv_values(self):
        for pv in si_pvs.read_only_pvs:
            self.setParam(pv, self.si_model.get_pv(pv))
        # for pv in bo_pvs.read_only_pvs:
        #     self.setParam(pv, self.bo_model.get_pv(pv))
        # for pv in ts_pvs.read_only_pvs:
        #     self.setParam(pv, self.ts_model.get_pv(pv))
        # for pv in tb_pvs.read_only_pvs:
        #     self.setParam(pv, self.tb_model.get_pv(pv))
        # for pv in li_pvs.read_only_pvs:
        #     self.setParam(pv, self.li_model.get_pv(pv))


class DriverThread(threading.Thread):

    def __init__(self, driver, stop_event):
        self._driver = driver
        self._stop_event = stop_event
        super().__init__(target=self._main)
        self._driver.update_sp_pv_values()   # inits SP fields from model

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
        server.process(WAIT_TIMEOUT)
