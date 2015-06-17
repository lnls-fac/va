
import sys
import time
import signal
import threading
from pcaspy import SimpleServer
import va.driver as pcasdriver
import va.model as models
import va.li_pvs as li_pvs
import va.tb_pvs as tb_pvs
import va.bo_pvs as bo_pvs
import va.ts_pvs as ts_pvs
import va.si_pvs as si_pvs
import va.ti_pvs as ti_pvs
import va.utils as utils
import va


WAIT_TIMEOUT = 0.1


class DriverThread(threading.Thread):

    def __init__(self, driver, stop_event):
        self._driver = driver
        self._stop_event = stop_event
        super().__init__(target=self._main)
        self._driver.init_sp_pv_values() # inits SP fields from model

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


def run(prefix):
    global stop_event, driver_thread

    li_pv_names = list(li_pvs.database.keys())
    tb_pv_names = list(tb_pvs.database.keys())
    bo_pv_names = list(bo_pvs.database.keys())
    ts_pv_names = list(ts_pvs.database.keys())
    si_pv_names = list(si_pvs.database.keys())
    ti_pv_names = list(ti_pvs.database.keys())

    utils.print_banner(prefix,
                      li_pv_names = li_pv_names,
                      tb_pv_names = tb_pv_names,
                      bo_pv_names = bo_pv_names,
                      ts_pv_names = ts_pv_names,
                      si_pv_names = si_pv_names,
                      ti_pv_names = ti_pv_names)

    li = models.LiModel(all_pvs=li_pvs.all_record_names)
    tb = models.TbModel(all_pvs=tb_pvs.all_record_names)
    bo = models.BoModel(all_pvs=bo_pvs.all_record_names)
    ts = models.TsModel(all_pvs=ts_pvs.all_record_names)
    si = models.SiModel(all_pvs=si_pvs.all_record_names)
    ti = models.TiModel(all_pvs=ti_pvs.all_record_names)

    stop_event = threading.Event()

    pvs_database = {}
    pvs_database.update(li_pvs.database)
    pvs_database.update(tb_pvs.database)
    pvs_database.update(bo_pvs.database)
    pvs_database.update(ts_pvs.database)
    pvs_database.update(si_pvs.database)
    pvs_database.update(ti_pvs.database)

    server = SimpleServer()
    server.createPV(prefix, pvs_database)

    driver = pcasdriver.PCASDriver(li_model = li,
                                   tb_model = tb,
                                   bo_model = bo,
                                   ts_model = ts,
                                   si_model = si,
                                   ti_model = ti,
                                   )

    driver_thread = DriverThread(driver, stop_event)
    driver_thread.start()

    signal.signal(signal.SIGINT, handle_signal)

    while not stop_event.is_set():
        server.process(WAIT_TIMEOUT)
