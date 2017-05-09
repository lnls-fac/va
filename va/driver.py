
import queue
import threading
import multiprocessing
import time
import numpy as _np
# import prctl #Used in debugging
from pcaspy import Driver
from . import utils


PREFIX_LEN = utils.PREFIX_LEN


class DriverThread(threading.Thread):

    def __init__(self, processes, interval,start_event, stop_event, finalisation):
        """Driver processing management

        Keyword arguments:
        driver -- pcaspy Driver object
        interval -- processing interval [s]
        stop_event -- event to stop processing
        finalisation -- barrier to wait before finalisation
        """
        self.my_queue = multiprocessing.Queue()
        self._interval = interval
        self._stop_event = stop_event
        self._finalisation = finalisation
        super().__init__(
            target=self._main,
            kwargs={'processes':processes,
                    'stop_event':stop_event,
                    'start_event':start_event,
                    'interval':interval,
                    'my_queue':self.my_queue
                    },
            name = 'Thread-Driver'
            )

    def _main(self,**kwargs):
        self._driver = PCASDriver(**kwargs)
        # prctl.set_name(self.name) # For debug
        try:
            while not self._stop_event.is_set():
                utils.process_and_wait_interval(self._driver.process,self._interval)
        except Exception as ex:
            utils.log('error', str(ex), 'red')
            self.stop_event.set()
        finally:
            self._driver.close_others_queues()
            self._finalisation.wait()
            self._driver.empty_my_queue()
            self._finalisation.wait()
            self._driver.finalise()


class PCASDriver(Driver):

    def  __init__(self, processes, start_event, stop_event, interval,my_queue):
        super().__init__()
        self._interval = interval
        self._start_event = start_event
        self._internal_queue = queue.Queue()
        self._my_queue = my_queue
        self._stop_event = stop_event
        self._processes = dict()
        self._processes_initialisation = dict()
        for p in processes:
            self._processes[p.area_structure_prefix] = p
            self._processes_initialisation[p.area_structure_prefix] = False

    def process(self):
        self._process_writes()
        self._process_requests()
        self.updatePVs()

    def _process_writes(self):
        size = self._internal_queue.qsize()
        for i in range(size):
            process, reason, value = self._internal_queue.get()
            process.my_queue.put(('s', (reason, value)))

    def _process_requests(self):
        size = self._my_queue.qsize()
        for _ in range(size):
            request = self._my_queue.get()
            self._process_request(request)

    def _process_request(self, request):
        cmd, data = request
        if cmd == 's': # set PV value in EPICS memory DB
            self._set_parameter_in_memory(data)
        elif cmd == 'sp': # initialise setpoints
            self._set_sp_parameters_in_memory(data)
        elif cmd == 'a': # anomalous condition signed by area_structure
            utils.log('!error', data, c='red')
            self._stop_event.set()
        elif cmd == 'i':
            self._initialisation_sign_received(data)
        else:
            utils.log('!cmd', cmd, c='red', a=['bold'])

    def _set_parameter_in_memory(self, data):
        pv_name, value = data
        self.setParam(pv_name, value)

    def _set_sp_parameters_in_memory(self, data):
        sp_pv_list = data
        for pv_name, value in sp_pv_list:
            if value is None: print(pv_name)
            self.setParam(pv_name, value)

    def _initialisation_sign_received(self, data):
        prefix = data
        self._processes_initialisation[prefix] = True
        if not self._start_event.is_set():
            if all(self._processes_initialisation.values()):
                self._start_event.set()

    def close_others_queues(self):
        for p in self._processes.values():
            p.my_queue.close()

    def empty_my_queue(self):
        while not self._my_queue.empty():
            self._my_queue.get()

    def finalise(self):
        self._my_queue.close()
        self._my_queue.join_thread()
        utils.log('exit', 'driver ')

    def read(self, reason):
        utils.log('read', reason, c='yellow')
        return super().read(reason)

    def write(self, reason, value):
        try:
            if reason == 'QUIT':
                if value == 0:
                    utils.log('quit', 'command received with zero value', c='yellow', a=['bold'])
                    return True
                utils.log('quit', 'quiting virtual machine', c='red', a=['bold'])
                self._stop_event.set()
                return True
            process = self._get_pv_process(reason)
            if self._is_process_pv_writable(process, reason):
                self.setParam(reason, value)
                # self.pvDB[reason].flag = False # avoid double camonitor update
                self._internal_queue.put((process, reason, value))
                if type(value) in (list, tuple, _np.ndarray) and len(value) > 10:
                    msg = reason + ' (' + str(len(value)) + ') ' \
                                 + str(value[0])  + ' ' + str(value[1]) \
                                 + ' ... ' \
                                 + str(value[-2]) + ' ' + str(value[-1])
                else:
                    msg = reason + ' ' + str(value)
                utils.log('write', msg, c='yellow', a=['bold'])
                return True
            else:
                utils.log('!write', reason, c='yellow', a=['bold'])
                return False
        except:
            utils.log('!write', reason, c='red', a=['bold'])
            return False

    def _get_pv_process(self, reason):
        prefix = reason[:PREFIX_LEN]
        process = self._processes[prefix]
        return process

    def _is_process_pv_writable(self, process, reason):
        read_only_pvs = process.area_structure.pv_module.get_read_only_pvs()
        dynamic_pvs = process.area_structure.pv_module.get_dynamical_pvs()
        return reason not in read_only_pvs + dynamic_pvs
