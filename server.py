#!/usr/bin/env python3

import sys
import time
import signal
import threading
from pcaspy import SimpleServer
import va.driver as pcasdriver
import va.model as models
import va.si_pvs as si_pvs
import va
#import va.bo_pvs as bo_pvs
#import va.ts_pvs as ts_pvs
#import va.tb_pvs as tb_pvs
#import va.li_pvs as li_pvs


WAIT_TIMEOUT = 0.1


class DriverThread(threading.Thread):

    def __init__(self, driver, stop_event):
        self._driver = driver
        self._stop_event = stop_event
        super().__init__(target=self._main)
        self._driver.update_sp_pv_values() # inits SP fields from model

    def _main(self):
        while True:
            t0 = time.time()
            self._driver.update_pvs()
            delta = time.time() - t0
            if self._stop_event.wait(WAIT_TIMEOUT - delta):
                break


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

    si_pv_names = list(si_pvs.database.keys())

    print()
    print('VirtualAccelerator')
    print('==================')
    print('{0:<15s}: {1}'.format('version:', va.__version__))
    print('{0:<15s}: "{1}"'.format('pv prefix', prefix))
    print('{0:<15s}: {1}'.format('# pvs in si', len(si_pv_names)))
    print()
    
    si = models.SiModel()
    stop_event = threading.Event()

    server = SimpleServer()
    server.createPV(prefix, si_pvs.database)

    driver = pcasdriver.PCASDriver(si)
    driver_thread = DriverThread(driver, stop_event)
    driver_thread.start()

    signal.signal(signal.SIGINT, handle_signal)

    while not stop_event.is_set():
        server.process(WAIT_TIMEOUT)
