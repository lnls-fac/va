#!/usr/bin/env python3

import signal
import multiprocessing
from pcaspy import SimpleServer
from . import driver
from . import model
from . import sirius_models
from . import utils

WAIT_TIMEOUT = 0.1
JOIN_TIMEOUT = 1.0


stop_event = multiprocessing.Event()


def run(prefix):
    """Start virtual accelerator with given PV prefix

    Keyword arguments:
    prefix -- prefix to be added to PVs
    """
    global stop_event

    set_sigint_handler(handle_signal)

    models = get_models()
    pv_database = get_pv_database(models)

    pv_names = get_pv_names(models)
    utils.print_banner(prefix, **pv_names)

    server = SimpleServer()
    server.createPV(prefix, pv_database)

    processes = start_model_processes(models, stop_event)

    start_driver_thread(processes, stop_event)

    while not stop_event.is_set():
        server.process(WAIT_TIMEOUT)

    join_processes(processes)

def set_sigint_handler(handler):
    signal.signal(signal.SIGINT, handle_signal)

def handle_signal(signum, frame):
    global stop_event
    stop_event.set()

def get_models():
    models = (
        sirius_models.LiModel,
        sirius_models.TbModel,
        sirius_models.BoModel,
        sirius_models.SiModel,
        sirius_models.TsModel,
        sirius_models.TiModel,
    )

    return models

def get_pv_database(models):
    pv_database = {}
    for m in models:
        pv_database.update(m.database)

    return pv_database

def get_pv_names(models):
    pv_names = {}
    for m in models:
        pv_names.update({m.prefix.lower()+'_pv_names': m.database.keys()})

    return pv_names

def start_model_processes(models, stop_event):
    processes = []
    for m in models:
        mp = model.ModelProcess(m, WAIT_TIMEOUT, stop_event)
        mp.start()
        processes.append(mp)

    return processes

def start_driver_thread(processes, stop_event):
    pcas_driver = driver.PCASDriver(processes)
    driver_thread = driver.DriverThread(pcas_driver, WAIT_TIMEOUT, stop_event)
    driver_thread.start()

def join_processes(processes):
    for process in processes:
        process.join(JOIN_TIMEOUT)
