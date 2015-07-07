#!/usr/bin/env python3

import time
import signal
import threading
import multiprocessing
from pcaspy import SimpleServer
from pcaspy import Driver
import va.sirius_models as models
import va.pvs_li as pvs_li
import va.pvs_tb as pvs_tb
import va.pvs_bo as pvs_bo
import va.pvs_ts as pvs_ts
import va.pvs_si as pvs_si
import va.pvs_ti as pvs_ti
import va.utils as utils


WAIT_TIMEOUT = 0.1


def run(prefix):
    """Start virtual accelerator with given PV prefix

    Keyword arguments:
    prefix -- prefix to be added to PVs
    """

    global stop_event
    stop_event = multiprocessing.Event()
    signal.signal(signal.SIGINT, handle_signal)

    li_pv_names = list(pvs_li.get_database().keys())
    tb_pv_names = list(pvs_tb.get_database().keys())
    bo_pv_names = list(pvs_bo.get_database().keys())
    ts_pv_names = list(pvs_ts.get_database().keys())
    si_pv_names = list(pvs_si.get_database().keys())
    ti_pv_names = list(pvs_ti.get_database().keys())

    utils.print_banner(prefix,
                      li_pv_names = li_pv_names,
                      tb_pv_names = tb_pv_names,
                      bo_pv_names = bo_pv_names,
                      ts_pv_names = ts_pv_names,
                      si_pv_names = si_pv_names,
                      ti_pv_names = ti_pv_names)

    pvs_database = {}
    pvs_database.update(pvs_li.get_database())
    pvs_database.update(pvs_tb.get_database())
    pvs_database.update(pvs_bo.get_database())
    pvs_database.update(pvs_ts.get_database())
    pvs_database.update(pvs_si.get_database())
    pvs_database.update(pvs_ti.get_database())

    server = SimpleServer()
    server.createPV(prefix, pvs_database)

    driver = PCASDriver(stop_event)
    driver_thread = DriverThread(driver, stop_event)
    driver_thread.start()

    while not stop_event.is_set():
        server.process(WAIT_TIMEOUT)


class DriverThread(threading.Thread):

    def __init__(self, driver, stop_event):
        self._driver = driver
        self._stop_event = stop_event
        super().__init__(target=self._main)

    def _main(self):
        while True:
            self._driver.process()
            if self._stop_event.is_set():
                print('Stop_event is set')
                for process in self._driver._model_process_list:
                    process.join()
                break

class PCASDriver(Driver):
    def  __init__(self, stop_event):
        super().__init__()
        self._stop_event = stop_event
        self._model_process_list = []
        self._p_ti = self.init_model_process('TI')
        self._p_li = self.init_model_process('LI')
        self._p_tb = self.init_model_process('TB')
        self._p_bo = self.init_model_process('BO')
        self._p_ts = self.init_model_process('TS')
        self._p_si = self.init_model_process('SI')

        self.read_only_pvs  = pvs_li.get_read_only_pvs() + \
                              pvs_tb.get_read_only_pvs() +\
                              pvs_bo.get_read_only_pvs() + \
                              pvs_ts.get_read_only_pvs() + \
                              pvs_si.get_read_only_pvs() + \
                              pvs_ti.get_read_only_pvs()
        self.read_write_pvs = pvs_li.get_read_write_pvs() + \
                              pvs_tb.get_read_write_pvs() + \
                              pvs_bo.get_read_write_pvs() + \
                              pvs_ts.get_read_write_pvs() + \
                              pvs_si.get_read_write_pvs() + \
                              pvs_ti.get_read_write_pvs()
        self.dynamic_pvs    = pvs_li.get_dynamical_pvs() + \
                              pvs_tb.get_dynamical_pvs() + \
                              pvs_bo.get_dynamical_pvs() + \
                              pvs_ts.get_dynamical_pvs() + \
                              pvs_si.get_dynamical_pvs() + \
                              pvs_ti.get_dynamical_pvs()

    def read(self, reason):
        utils.log('read',reason,c='yellow')
        return super().read(reason)

    def write(self, reason, value):
        if reason in self.read_only_pvs:
            utils.log('!write',reason + ' ' + str(value), c='yellow', a=['bold'])
        else:
            utils.log('write', reason + ' ' + str(value), c='yellow', a=['bold'])
            if reason.startswith('LI'):
                self._p_li.send((reason, value))
            elif reason.startswith('TB'):
                self._p_tb.send((reason, value))
            elif reason.startswith('BO'):
                self._p_bo.send((reason, value))
            elif reason.startswith('TS'):
                self._p_ts.send((reason, value))
            elif reason.startswith('SI'):
                self._p_si.send((reason, value))
            elif reason.startswith('TI'):
                self._p_ti.send((reason, value))
            else:
                raise Exception('System not found')
            self.setParam(reason, value)

    def init_model_process(self, model, r=None):
        if model == 'LI':
            target = LiModel
        elif model == 'TB':
            target = TbModel
        elif model == 'BO':
            target = BoModel
        elif model == 'TS':
            target = TsModel
        elif model == 'SI':
            target = SiModel
        elif model == 'TI':
            target = TiModel
        else:
            raise Exception('Subsystem not found')
        p_driver, p_model = multiprocessing.Pipe()
        model_process = multiprocessing.Process(target=target, args=(self._stop_event, model, p_model))
        self._model_process_list.append(model_process)
        model_process.start()
        return p_driver

    def process(self):
        if self._p_li.poll():
            pv_name, value = self._p_li.recv()
            self.setParam(pv_name, value)
        if self._p_tb.poll():
            pv_name, value = self._p_tb.recv()
            self.setParam(pv_name, value)
        if self._p_bo.poll():
            pv_name, value = self._p_bo.recv()
            self.setParam(pv_name, value)
        if self._p_ts.poll():
            pv_name, value = self._p_ts.recv()
            self.setParam(pv_name, value)
        if self._p_si.poll():
            pv_name, value = self._p_si.recv()
            self.setParam(pv_name, value)
        if self._p_ti.poll():
            pv_name, value = self._p_ti.recv()
            self.setParam(pv_name, value)


class Model(object):

    def __init__(self, stop_event, model, pipe):
        self._stop_event = stop_event
        self._model = model
        self._pipe = pipe
        self.process()

    def process(self):
        while not self._stop_event.is_set():
            if self._pipe.poll():
                pv_name, value = self._pipe.recv()
                value += 1
                self._pipe.send((pv_name,value))
            else:
                time.sleep(0.0001)

class LiModel(Model):
    def __init__(self, stop_event, model, pipe):
        super().__init__(stop_event, model, pipe)

class TbModel(Model):
    def __init__(self, stop_event, model, pipe):
        super().__init__(stop_event, model, pipe)

class BoModel(Model):
    def __init__(self, stop_event, model, pipe):
        super().__init__(stop_event, model, pipe)

class TsModel(Model):
    def __init__(self, stop_event, model, pipe):
        super().__init__(stop_event, model, pipe)

class SiModel(Model):
    def __init__(self, stop_event, model, pipe):
        super().__init__(stop_event, model, pipe)

class TiModel(Model):
    def __init__(self, stop_event, model, pipe):
        super().__init__(stop_event, model, pipe)

def handle_signal(signum, frame):
    global stop_event
    stop_event.set()
