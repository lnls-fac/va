
import sys
import time
import signal
import threading
from pcaspy import SimpleServer
import va.driver as pcasdriver
import va.sirius_models as models
import va.pvs.li as pvs_li
import va.pvs.tb as pvs_tb
import va.pvs.bo as pvs_bo
import va.pvs.ts as pvs_ts
import va.pvs.si as pvs_si
import va.pvs.ti as pvs_ti
import va.utils as utils
import va


WAIT_TIMEOUT = 0.1


def run(prefix):
    """Start virtual accelerator with given PV prefix

    Keyword arguments:
    prefix -- prefix to be added to PVs
    """
    global stop_event, driver_thread

    utils.print_banner(prefix,
                      li_pv_names = list(pvs_li.get_database().keys()),
                      tb_pv_names = list(pvs_tb.get_database().keys()),
                      bo_pv_names = list(pvs_bo.get_database().keys()),
                      ts_pv_names = list(pvs_ts.get_database().keys()),
                      si_pv_names = list(pvs_si.get_database().keys()),
                      ti_pv_names = list(pvs_ti.get_database().keys()))

    li = models.LiModel(all_pvs=pvs_li.get_all_record_names())
    tb = models.TbModel(all_pvs=pvs_tb.get_all_record_names())
    bo = models.BoModel(all_pvs=pvs_bo.get_all_record_names())
    ts = models.TsModel(all_pvs=pvs_ts.get_all_record_names())
    si = models.SiModel(all_pvs=pvs_si.get_all_record_names())
    ti = models.TiModel(all_pvs=pvs_ti.get_all_record_names())

    pvs_database = {}
    pvs_database.update(pvs_li.get_database())
    pvs_database.update(pvs_tb.get_database())
    pvs_database.update(pvs_bo.get_database())
    pvs_database.update(pvs_ts.get_database())
    pvs_database.update(pvs_si.get_database())
    pvs_database.update(pvs_ti.get_database())

    server = SimpleServer()
    server.createPV(prefix, pvs_database)

    driver = pcasdriver.PCASDriver(li_model = li,
                                   tb_model = tb,
                                   bo_model = bo,
                                   ts_model = ts,
                                   si_model = si,
                                   ti_model = ti,
                                   )

    driver.all_models_defined_ack() # so that models can set its parameters that
                                    # are dependent on other models

    stop_event = threading.Event()
    driver_thread = DriverThread(driver, stop_event)
    driver_thread.start()

    signal.signal(signal.SIGINT, handle_signal)

    while not stop_event.is_set():
        server.process(WAIT_TIMEOUT)


class DriverThread(threading.Thread):

    def __init__(self, driver, stop_event):
        self._driver = driver
        self._stop_event = stop_event
        super().__init__(target=self._main)
        self._driver.init_sp_pv_values() # initialise SP fields from model

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
