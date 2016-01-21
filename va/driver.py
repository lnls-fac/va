
import queue
import threading
from pcaspy import Driver
from . import utils


PREFIX_LEN = utils.PREFIX_LEN


class DriverThread(threading.Thread):

    def __init__(self, driver, interval, stop_event, finalisation):
        """Driver processing management

        Keyword arguments:
        driver -- pcaspy Driver object
        interval -- processing interval [s]
        stop_event -- event to stop processing
        finalisation -- barrier to wait before finalisation
        """
        self._driver = driver
        self._interval = interval
        self._stop_event = stop_event
        self._finalisation = finalisation
        super().__init__(target=self._main)

    def _main(self):
        while not self._stop_event.is_set():
            utils.process_and_wait_interval(
                self._driver.process,
                self._interval
            )
        else:
            self._finalisation.wait()
            self._finalisation.wait()
            self._driver.finalise()


class PCASDriver(Driver):

    def  __init__(self, processes, start_event, stop_event, interval):
        super().__init__()
        self._interval = interval
        self._start_event = start_event
        self._queue = queue.Queue()
        self._stop_event = stop_event
        self._processes = dict()
        self._processes_initialisation = dict()
        for p in processes:
            self._processes[p.model_prefix] = p
            self._processes_initialisation[p.model_prefix] = False

    def process(self):
        self._process_writes()
        self._process_requests()
        self.updatePVs()

    def _process_writes(self):
        size = self._queue.qsize()
        for i in range(size):
            process, reason, value = self._queue.get()
            if "SIDI-BPM" in reason: print(reason)
            process.send_queue.put(('s', (reason, value)))

    def _process_requests(self):
        for process in self._processes.values():
            recv_queue = process.recv_queue
            while not recv_queue.empty():
                request = recv_queue.get()
                self._process_request(request)

    def _process_request(self, request):
        cmd, data = request
        if cmd == 's': # set PV value in EPICS memory DB
            self._set_parameter_in_memory(data)
        elif cmd == 'p': # pass to model
            self._pass_to_model(data)
        elif cmd == 'sp': # initialise setpoints
            self._set_sp_parameters_in_memory(data)
        elif cmd == 'a': # anomalous condition signed by model
            utils.log('!error', data, c='red')
            self._stop_event.set()
        elif cmd == 'i':
            self._initialisation_sign_received(data)
        else:
            utils.log('!cmd', cmd, c='red', a=['bold'])

    def _set_parameter_in_memory(self, data):
        pv_name, value = data
        self.setParam(pv_name, value)

    def _pass_to_model(self, data):
        prefix, args_dict = data
        self._send_to_model('p', prefix, args_dict)

    def _set_sp_parameters_in_memory(self, data):
        sp_pv_list = data
        for pv_name, value in sp_pv_list:
            self.setParam(pv_name, value)

    def _send_to_model(self, cmd, prefix, args):
        try:
            process = self._processes[prefix]
            process.send_queue.put((cmd, args))
        except:
            utils.log('!pref', prefix, c='red', a=['bold'])

    def _initialisation_sign_received(self, data):
        prefix = data
        self._processes_initialisation[prefix] = True
        if not self._start_event.is_set():
            if all(self._processes_initialisation.values()):
                self._start_event.set()

    def finalise(self):
        for p in self._processes.values():
            p.send_queue.close()
            p.send_queue.join_thread()
            p.recv_queue.close()
            p.recv_queue.join_thread()

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
                self.pvDB[reason].flag = False # avoid double camonitor update
                self._queue.put((process, reason, value))
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
        read_only_pvs = process.model.pv_module.get_read_only_pvs()
        dynamic_pvs = process.model.pv_module.get_dynamical_pvs()
        return reason not in read_only_pvs + dynamic_pvs
