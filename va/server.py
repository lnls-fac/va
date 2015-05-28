
import sys
import time
import signal
import threading
from pcaspy import SimpleServer
import va.driver as pcasdriver
import va.model as models
import va.li_pvs as li_pvs
import va.bo_pvs as bo_pvs
import va.si_pvs as si_pvs
import va.ti_pvs as ti_pvs
import va
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


def run():
    if len(sys.argv) > 1:
        prefix = sys.argv[1]
    else:
        raise Exception('Please provide a prefix!')

    li_pv_names = list(li_pvs.database.keys())
    bo_pv_names = list(bo_pvs.database.keys())
    si_pv_names = list(si_pvs.database.keys())
    ti_pv_names = list(ti_pvs.database.keys())

    utils.print_banner(prefix,
                      li_pv_names = li_pv_names,
                      bo_pv_names = bo_pv_names,
                      si_pv_names = si_pv_names,
                      ti_pv_names = ti_pv_names)

    li = models.LiModel()
    bo = models.BoModel()
    si = models.SiModel()
    ti = models.TiModel()

    stop_event = threading.Event()

    pvs_database = {}
    pvs_database.update(li_pvs.database)
    pvs_database.update(bo_pvs.database)
    pvs_database.update(si_pvs.database)
    pvs_database.update(ti_pvs.database)

    server = SimpleServer()
    server.createPV(prefix, pvs_database)

    driver = pcasdriver.PCASDriver(li_model = li,
                                   bo_model = bo,
                                   si_model = si,
                                   ti_model = ti)

    driver_thread = DriverThread(driver, stop_event)
    driver_thread.start()

    signal.signal(signal.SIGINT, handle_signal)

    while not stop_event.is_set():
        server.process(WAIT_TIMEOUT)
