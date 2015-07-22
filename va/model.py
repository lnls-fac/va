
import time
import multiprocessing
import threading
from . import utils


class ModelProcess(multiprocessing.Process):

    def __init__(self, model, interval, stop_event):
        conn1, conn2 = multiprocessing.Pipe()
        self.pipe = conn1
        self.model = model
        super().__init__(
            target=start_and_run_model,
            kwargs={
                'model': model,
                'stop_event': stop_event,
                'pipe': conn2,
                'interval': interval,
            }
        )

def start_and_run_model(model, stop_event, interval, **kwargs):
    """Start periodic processing of model

    Keyword arguments:
    model -- model class
    stop_event -- multiprocessing.Event for stopping model
    interval -- processing interval [s]
    **kwargs -- extra arguments to model __init__
    """
    m = model(interval=interval, **kwargs)
    m_thread = ModelThread(m, interval, stop_event)
    m_thread.start()
    while not stop_event.is_set():
        utils.process_and_wait_interval(m.process, interval)


class Model:

    def __init__(self, pipe, interval, log_func=utils.log, **kwargs):
        self._pipe = pipe
        self._all_pvs = self.pv_module.get_all_record_names()
        self._log = log_func
        self._interval = interval/2
        self._state_deprecated = True

    def process(self):
        self._process_requests()
        self._update_state()

    def update_pvs(self):
        if self._state_deprecated:
            for pv in self.pv_module.get_read_only_pvs() + self.pv_module.get_dynamical_pvs():
                value = self._get_pv(pv)
                self._pipe.send(('s', (pv, value)))
        else:
            for pv in self.pv_module.get_dynamical_pvs():
                value = self._get_pv(pv)
                self._pipe.send(('s', (pv, value)))

    def _process_requests(self):
        start_time = time.time()
        while self._has_remaining_time_and_request(start_time):
            cmd, data = self._pipe.recv()
            if cmd == 's':
                pv_name, value = data
                self._set_pv(pv_name, value)
            elif cmd == 'p':
                function, args_dict = data
                self._execute_function(function=function, **args_dict)
            else:
                print('Invalid command:', cmd)

    def _has_remaining_time_and_request(self, start_time):
        has_remaining_time = (time.time() - start_time) < self._interval
        has_request = self._pipe.poll()
        return has_remaining_time and has_request

    def _init_sp_pv_values(self):
        utils.log('init', 'epics sp memory for %s pvs'%self.prefix)
        for pv in self.pv_module.get_read_write_pvs():
            value = self._get_pv(pv)
            self._pipe.send(('s', (pv, value)))

    def _execute_function(self, function=None, **kwargs):
        if function == 'get_parameters_from_upstream_accelerator':
            self._get_parameters_from_upstream_accelerator(**kwargs)

class ModelThread(threading.Thread):

    def __init__(self, model, interval, stop_event):
        self._model = model
        self._interval = interval
        self._stop_event = stop_event
        super().__init__(target=self._main)

    def _main(self):
        while not self._stop_event.is_set():
            start_time = time.time()
            self._model.update_pvs()
            delta_t = time.time() - start_time
            if 0 < delta_t < self._interval:
                time.sleep(self._interval - delta_t)
