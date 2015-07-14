#!/usr/bin/env python3

import signal
import multiprocessing
from pcaspy import SimpleServer
import sirius
from . import model
from . import sirius_models
from . import driver


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

    models = (
        sirius_models.SiModel,
        sirius_models.BoModel,
    )

    pvs_database = {}
    processes = []
    for m in models:
        pvs_database.update(m.database)
        mp = model.ModelProcess(m, WAIT_TIMEOUT, stop_event)
        mp.start()
        processes.append(mp)

    server = SimpleServer()
    server.createPV(prefix, pvs_database)

    pcas_driver = driver.PCASDriver(processes)
    driver_thread = driver.DriverThread(pcas_driver, WAIT_TIMEOUT, stop_event)
    driver_thread.start()

    while not stop_event.is_set():
        server.process(WAIT_TIMEOUT)

    for process in processes:
        process.join(JOIN_TIMEOUT)


def handle_signal(signum, frame):
    global stop_event
    stop_event.set()
