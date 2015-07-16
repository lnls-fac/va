
import time
import multiprocessing
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
    while not stop_event.is_set():
        utils.process_and_wait_interval(m.process, interval)


class Model:

    def __init__(self, pipe, interval, log_func=utils.log, **kwargs):
        self._pipe = pipe
        self._all_pvs = self.pv_module.get_all_record_names()
        self._log = log_func
        self._interval = interval/2

    def process(self):
        self._process_requests()
        self._update_state()
        self._send_responses()

    def _process_requests(self):
        start_time = time.time()
        while self._has_remaining_time_and_request(start_time):
            pv_name, value = self._pipe.recv()
            self._set_pv(pv_name, value)

    def _has_remaining_time_and_request(self, start_time):
        has_remaining_time = (time.time() - start_time) < self._interval
        has_request = self._pipe.poll()
        return has_remaining_time and has_request

    def _update_state(self):
        pass

    def _send_responses(self):
        pass

    def _set_pv(self, name, value):
        pass
