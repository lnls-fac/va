"""Module with Virtual Accelerator driver."""

import queue
import threading
import multiprocessing
import numpy as _np
from pcaspy import Driver
from va import utils


PREFIX_LEN = utils.PREFIX_LEN


class DriverThread(threading.Thread):
    """Thread where driver will run."""

    def __init__(self, processes, interval,
                 start_event, stop_event, finalisation):
        """Driver processing management.

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
            kwargs={'processes': processes,
                    'stop_event': stop_event,
                    'start_event': start_event,
                    'interval': interval,
                    'my_queue': self.my_queue
                    },
            name='Thread-Driver'
            )

    def _main(self, **kwargs):
        self._driver = PCASDriver(**kwargs)
        # prctl.set_name(self.name) # For debug
        try:
            while not self._stop_event.is_set():
                utils.process_and_wait_interval(self._driver.process,
                                                self._interval)
        except Exception as ex:
            utils.log('error', 'in driver main: ' + str(ex), 'red')
            self.stop_event.set()
        finally:
            self._driver.close_others_queues()
            self._finalisation.wait()
            self._driver.empty_my_queue()
            self._finalisation.wait()
            self._driver.finalise()

class PCASDriver(Driver):
    """Driver Definition."""

    def __init__(self, processes, start_event,
                 stop_event, interval, my_queue):
        """Instance Initialization."""
        super().__init__()
        self._interval = interval
        self._start_event = start_event
        self._internal_queue = queue.Queue()
        self._my_queue = my_queue
        self._stop_event = stop_event
        self._processes = dict()
        self._processes_database = dict()
        self._processes_initialisation = dict()
        for p in processes:
            prefix = p.area_structure_prefix
            self._processes[prefix] = p
            self._processes_initialisation[prefix] = False
            self._processes_database[prefix] = \
                p.area_structure.pv_module.get_database()

    def process(self):
        """Function that run continuously."""
        statusw = self._process_writes()
        statusr = self._process_requests()
        if statusw or statusr:
            self.updatePVs()  # NOTE: should we update all PVs?

    def _process_writes(self):
        size = self._internal_queue.qsize()
        for _ in range(size):
            process, reason, value = self._internal_queue.get()
            process.my_queue.put(('s', (reason, value)))
        return size > 0

    def _process_requests(self):
        size = self._my_queue.qsize()
        for _ in range(size):
            request = self._my_queue.get()
            self._process_request(request)
        return size > 0

    def _process_request(self, request):
        cmd, data = request
        if cmd == 's':  # set PV value in EPICS memory DB
            self._set_parameter_in_memory(data)
        elif cmd == 'sp':  # initialise setpoints
            self._set_sp_parameters_in_memory(data)
        elif cmd == 'a':  # anomalous condition signed by area_structure
            utils.log('!error3', data, c='red')
            self._stop_event.set()
        elif cmd == 'i':  # initialisation signaling
            self._initialisation_sign_received(data)
        else:
            utils.log('!cmd', cmd, c='red', a=['bold'])

    def _set_parameter_in_memory(self, data):
        pv_name, value = data
        try:
            self.setParam(pv_name, value)
        except:
            print('error in setParam: ', pv_name, value)
            raise

    def _set_sp_parameters_in_memory(self, data):
        sp_pv_list = data
        for pv_name, value in sp_pv_list:
            if value is None:
                utils.log(
                    'warn', 'Value for {} is None!'.format(pv_name), 'yellow')
            else:
                self.setParam(pv_name, value)

    def _initialisation_sign_received(self, data):
        prefix = data
        if self._processes_initialisation[prefix]:
            return
        self._processes_initialisation[prefix] = True
        # print(self._processes_initialisation)
        utils.log('init', 'area_structure {} initialised (requests in driver queue: {})'.format(prefix, self._my_queue.qsize()), 'green')
        if not self._start_event.is_set():
            if all(self._processes_initialisation.values()):
                self._start_event.set()

    def close_others_queues(self):
        """Close other processess queues."""
        for p in self._processes.values():
            p.my_queue.close()

    def empty_my_queue(self):
        """Empty the driver queue."""
        while not self._my_queue.empty():
            self._my_queue.get()

    def finalise(self):
        """Finalise properly."""
        self._my_queue.close()
        self._my_queue.join_thread()
        utils.log('exit', 'driver ')

    def read(self, reason):
        """Read PV value from database."""
        utils.log('read', reason, c='yellow')
        return super().read(reason)

    def write(self, reason, value):
        """Write PV value to database."""
        # process VACA pvs first
        if self._write_vaca_pvs(reason, value):
            return True
        try:
            process = self._get_pv_process(reason)
            if self._isValid(process, reason, value):
                self.setParam(reason, value)
                self._internal_queue.put((process, reason, value))
                if type(value) in (list, tuple,
                                   _np.ndarray) and len(value) > 10:
                    msg = reason + ' (' + str(len(value)) + ') ' \
                                 + str(value[0]) + ' ' + str(value[1]) \
                                 + ' ... ' \
                                 + str(value[-2]) + ' ' + str(value[-1])
                else:
                    msg = reason + ' ' + str(value)
                utils.log('write', msg, c='yellow', a=['bold'])
                return True
            else:
                utils.log('!write', reason, c='yellow', a=['bold'])
                return False
        except Exception:
            utils.log('!write', reason, c='red', a=['bold'])
            return False

    def _write_vaca_pvs(self, reason, value):
        if reason == 'AS-Glob:VA-Control:Quit-Cmd':
            utils.log('quit', 'quitting virtual machine', c='red', a=['bold'])
            self._stop_event.set()
            return True
        return False

    def _isValid(self, process, reason, value):
        if reason.endswith(('-Sts', '-RB', '-Mon')):
            return False
        db = self._processes_database[process.area_structure_prefix]
        if reason not in db:
            # for VACA pvs.
            return True
        enums = (db[reason].get('enums') or db[reason].get('Enums'))
        if enums is not None:
            if isinstance(value, int):
                len_ = len(enums)
                if value >= len_:
                    return False
            elif isinstance(value, str):
                if value not in enums:
                    return False
        return True

    def _get_pv_process(self, reason):
        prefix = reason[:PREFIX_LEN]
        process = self._processes[prefix]
        return process
