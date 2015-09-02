
import multiprocessing
import time
from . import utils


class ModelProcess(multiprocessing.Process):

    def __init__(self, model, interval, stop_event, finalisation):
        """Initialise, start and manage model and model processing.

        Keyword arguments: see start_and_run_model
        """
        send_queue = multiprocessing.Queue()
        recv_queue = multiprocessing.Queue()
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.model = model
        self.model_prefix = model.prefix

        super().__init__(
            target=start_and_run_model,
            kwargs={
                'model': model,
                'interval': interval,
                'stop_event': stop_event,
                # Queues are supposed to be exchanged
                'send_queue': recv_queue,
                'recv_queue': send_queue,
                'finalisation': finalisation,
            }
        )


def start_and_run_model(model, interval, stop_event, finalisation, **kwargs):
    """Start periodic processing of model

    Keyword arguments:
    model -- model class
    interval -- processing interval [s]
    stop_event -- event to stop processing
    finalisation -- barrier to wait before finalisation
    **kwargs -- extra arguments to model __init__
    """
    m = model(**kwargs)
    while not stop_event.is_set():
        utils.process_and_wait_interval(m.process, interval)
    else:
        finalisation.wait()
        m.empty_queues()
        finalisation.wait()
        m.finalise()


class Model:

    def __init__(self, send_queue, recv_queue, log_func=utils.log, **kwargs):
        self._send_queue = send_queue
        self._recv_queue = recv_queue
        self._all_pvs = self.pv_module.get_all_record_names()
        self._log = log_func
        self._state_changed = False

    def process(self):
        self._process_requests()
        self._update_state()
        self._update_pvs()

    def _process_requests(self):
        while not self._recv_queue.empty():
            request = self._recv_queue.get()
            self._process_request(request)

    def _process_request(self, request):
        cmd, data = request
        if cmd == 's':
            self._set_parameter(data)
        elif cmd == 'g':
            self._receive_parameter_value(data)
        elif cmd == 'p':
            self._execute_function(data)
        else:
            utils.log('!cmd', cmd, c='red', a=['bold'])

    def _set_parameter(self, data):
        pv_name, value = data
        self._set_pv(pv_name, value)

    def _receive_parameter_value(self, data):
        pv_name, value = data
        self._receive_pv_value(pv_name, value)

    def _execute_function(self, data):
        function, args_dict = data
        if function == 'get_parameters_from_upstream_accelerator':
            self._get_parameters_from_upstream_accelerator(args_dict)
        if function == 'get_charge_from_upstream_accelerator':
            self._get_charge_from_upstream_accelerator(args_dict)
        if function == 'receive_timing_signal':
            self._receive_timing_signal(args_dict)

    def _update_pvs(self):
        if self._state_changed:
            for pv in self.pv_module.get_read_only_pvs() + self.pv_module.get_dynamical_pvs():
                value = self._get_pv(pv)
                self._send_queue.put(('s', (pv, value)))
            self._state_changed = False
        else:
            for pv in self.pv_module.get_dynamical_pvs():
                value = self._get_pv(pv)
                self._send_queue.put(('s', (pv, value)))

    def empty_queues(self):
        while not self._send_queue.empty():
            self._send_queue.get()
        while not self._recv_queue.empty():
            self._recv_queue.get()

    def finalise(self):
        self._send_queue.close()
        self._send_queue.join_thread()
        self._recv_queue.close()
        self._recv_queue.join_thread()
