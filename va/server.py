#!/usr/bin/env python3

import time
import signal
import multiprocessing
import pcaspy
from . import driver
from . import area_structure
from . import sirius_area_structures
from . import utils

WAIT_TIMEOUT = 0.1
JOIN_TIMEOUT = 10.0
INIT_TIMEOUT = 20.0


def run(prefix):
    """Start virtual accelerator with given PV prefix

    Keyword arguments:
    prefix -- prefix to be added to PVs
    """
    global start_event
    global stop_event
    start_event = multiprocessing.Event()
    stop_event = multiprocessing.Event() # signals a stop request
    set_sigint_handler(set_global_stop_event)

    area_structures = get_area_structures()
    pv_database = get_pv_database(area_structures)
    pv_names = get_pv_names(area_structures)
    utils.print_banner(prefix, **pv_names)

    server = pcaspy.SimpleServer()
    server.createPV(prefix, pv_database)

    num_parties = len(area_structures) + 1 # number of parties for barrier
    finalisation_barrier = multiprocessing.Barrier(num_parties, timeout=JOIN_TIMEOUT)

    processes = create_area_structure_processes(area_structures, stop_event, finalisation_barrier)
    start_area_structure_processes(processes)
    start_driver_thread(processes, stop_event, start_event, finalisation_barrier)

    wait_for_initialisation()
    while not stop_event.is_set():
        server.process(WAIT_TIMEOUT)

    print_stop_event_message()
    join_processes(processes)


def set_sigint_handler(handler):
    signal.signal(signal.SIGINT, handler)


def set_global_stop_event(signum, frame):
    global stop_event
    stop_event.set()


def get_area_structures():
    area_structures = (
        sirius_area_structures.ASModel,
        sirius_area_structures.LiModel,
        sirius_area_structures.TbModel,
        sirius_area_structures.BoModel,
        sirius_area_structures.TsModel,
        sirius_area_structures.SiModel,
    )

    return area_structures


def get_pv_database(area_structures):
    pv_database = {}
    for As in area_structures:
        pv_database.update(As.database)
    pv_database['QUIT'] = {'type':'float', 'value':0, 'count':1}
    return pv_database


def get_pv_names(area_structures):
    pv_names = {}
    for As in area_structures:
        # Too low level?
        area_structure_pv_names = {As.prefix.lower()+'_pv_names': As.database.keys()}
        pv_names.update(area_structure_pv_names)

    return pv_names


def create_area_structure_processes(area_structures, stop_event, finalisation_barrier):
    processes = []
    for As in area_structures:
        Asp = area_structure.AreaStructureProcess(As, WAIT_TIMEOUT, stop_event,
            finalisation_barrier)
        processes.append(Asp)

    return processes


def start_area_structure_processes(processes):
    for p in processes:
        p.start()


def start_driver_thread(processes, stop_event, start_event, finalisation_barrier):
    pcas_driver = driver.PCASDriver(processes, start_event, stop_event, WAIT_TIMEOUT)
    driver_thread = driver.DriverThread(
        pcas_driver,
        WAIT_TIMEOUT,
        stop_event,
        finalisation_barrier
    )
    driver_thread.start()


def wait_for_initialisation():
    global start_event
    global stop_event
    t0 = time.time()
    utils.log('start', 'waiting area structure initialisation')
    while not start_event.is_set() and not stop_event.is_set():
        time.sleep(WAIT_TIMEOUT)
        t = time.time()
        if (t-t0) > INIT_TIMEOUT: break
    if not stop_event.is_set():
        utils.log('start', 'starting server', 'green')


def print_stop_event_message():
    utils.log('exit', 'stop_event was set', 'red')


def join_processes(processes):
    utils.log('join', 'joining processes...')
    for process in processes:
        process.join(JOIN_TIMEOUT)
    utils.log('join', 'done')


def old_wait_for_initialisation(interval):
    utils.log('start', 'waiting %d s for area structure initialisation' % interval)
    time.sleep(JOIN_TIMEOUT)
    utils.log('start', 'starting server')
