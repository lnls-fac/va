#!/usr/bin/env python3

import time
import signal
import multiprocessing
from pcaspy import SimpleServer
import sirius
from . import model
from . import sirius_models
from . import driver
from .pvs import si as pvs_si


WAIT_TIMEOUT = 0.1
JOIN_TIMEOUT = 1.0


stop_event = multiprocessing.Event()


def run(prefix):
    """Start virtual accelerator with given PV prefix

    Keyword arguments:
    prefix -- prefix to be added to PVs
    """
    global stop_event
    signal.signal(signal.SIGINT, handle_signal)

    si_model = sirius_models.SiModel

    pvs_database = {}
    pvs_database.update(si_model.pv_module.get_database())

    server = SimpleServer()
    server.createPV(prefix, pvs_database)

    processes = []
    si_process = model.ModelProcess(si_model, WAIT_TIMEOUT, stop_event)
    processes.append(si_process)

    si_process.start()

    pcas_driver = driver.PCASDriver(stop_event)
    driver_thread = driver.DriverThread(pcas_driver, stop_event)
    driver_thread.start()

    while not stop_event.is_set():
        server.process(WAIT_TIMEOUT)

    for process in processes:
        process.join(JOIN_TIMEOUT)


def handle_signal(signum, frame):
    global stop_event
    stop_event.set()
