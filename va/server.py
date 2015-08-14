#!/usr/bin/env python3

import signal
import multiprocessing
import pcaspy
from . import driver
from . import model
from . import sirius_models
from . import utils


WAIT_TIMEOUT = 0.1
JOIN_TIMEOUT = 1.0


def run(prefix):
    """Start virtual accelerator with given PV prefix

    Keyword arguments:
    prefix -- prefix to be added to PVs
    """
    global stop_event
    stop_event = multiprocessing.Event() # signals a stop request
    set_sigint_handler(set_global_stop_event)

    models = get_models()
    pv_database = get_pv_database(models)
    pv_names = get_pv_names(models)
    utils.print_banner(prefix, **pv_names)

    server = pcaspy.SimpleServer()
    server.createPV(prefix, pv_database)

    processes = create_model_processes(models, stop_event)
    start_model_processes(processes)
    start_driver_thread(processes, stop_event)

    while not stop_event.is_set():
        server.process(WAIT_TIMEOUT)

    print_exit_message()
    join_processes(processes)


def set_sigint_handler(handler):
    signal.signal(signal.SIGINT, handler)


def set_global_stop_event(signum, frame):
    global stop_event
    stop_event.set()


def get_models():
    models = (
        sirius_models.LiModel,
        sirius_models.TbModel,
        sirius_models.BoModel,
        sirius_models.TsModel,
        sirius_models.SiModel,
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
        # Too low level?
        model_pv_names = {m.prefix.lower()+'_pv_names': m.database.keys()}
        pv_names.update(model_pv_names)

    return pv_names


def create_model_processes(models, stop_event):
    processes = []
    for m in models:
        mp = model.ModelProcess(m, WAIT_TIMEOUT, stop_event)
        processes.append(mp)

    return processes


def start_model_processes(processes):
    for p in processes:
        p.start()


def start_driver_thread(processes, stop_event):
    pcas_driver = driver.PCASDriver(processes, WAIT_TIMEOUT)
    driver_thread = driver.DriverThread(pcas_driver, WAIT_TIMEOUT, stop_event)
    driver_thread.start()


def print_exit_message():
    utils.log('exit', 'stop_event was set')


def join_processes(processes):
    utils.log('join', 'joining processes...')
    for process in processes:
        process.join(JOIN_TIMEOUT)
    utils.log('join', 'done')
