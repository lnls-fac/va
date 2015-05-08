#!/usr/bin/env python3

import sys
import time
import signal
import threading
from pcaspy import SimpleServer
import va.driver as pcasdriver
import va.model as models
import va.si_pvs as si_pvs
import va.bo_pvs as bo_pvs
import va
from termcolor import colored
import utils


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
    bo_pv_names = list(bo_pvs.database.keys())

    color1 = 'white'
    color2 = 'red'
    print()
    print(colored('                    | A virtual accelerator for the SIRIUS project', color1, attrs=['bold']))
    print(' ' + colored('VirtualAccelerator', color2, attrs=['bold', 'underline']) + colored(' | Documentation: http://10.0.21.132', color1, attrs=['bold']))
    print('                    ' + colored('| Accelerator Physics Group', color1, attrs=['bold']))
    print('                    ' + colored('| Version {0}'.format(va.__version__), color1, attrs=['bold']))
    print('                    ' + colored('| Prefix: {0}'.format(prefix), color1, attrs=['bold']))
    print('                    ' + colored('| Number of SI pvs: {0}'.format(len(si_pv_names)), color1, attrs=['bold']))
    print('                    ' + colored('| Number of BO pvs: {0}'.format(len(bo_pv_names)), color1, attrs=['bold']))
    print()

    si = models.SiModel()
    bo = models.BoModel()
    stop_event = threading.Event()

    pvs_database = {}
    pvs_database.update(si_pvs.database)
    pvs_database.update(bo_pvs.database)

    server = SimpleServer()
    server.createPV(prefix, pvs_database)

    driver = pcasdriver.PCASDriver(si_model = si, bo_model = bo)
    driver_thread = DriverThread(driver, stop_event)
    driver_thread.start()

    signal.signal(signal.SIGINT, handle_signal)

    while not stop_event.is_set():
        server.process(WAIT_TIMEOUT)
