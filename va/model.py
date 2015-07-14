
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
        start_time = time.time()
        m.process()
        delta_t = time.time() - start_time
        if 0 < delta_t < interval:
            time.sleep(interval - delta_t)


class Model:

    def __init__(self, pipe, interval, log_func=utils.log, **kwargs):
        self._pipe = pipe
        self._all_pvs = self.pv_module.get_all_record_names()
        self._log = log_func
        self._interval = interval/2

    def process(self):
        self._receive_requests()
        self._update_state()
        self._send_responses()

    def _receive_requests(self):
        start_time = time.time()
        while (time.time()-start_time < self._interval) and self._pipe.poll():
            pv_name, value = self._pipe.recv()
            self._set_pv(pv_name, value)

    def _update_state(self):
        pass

    def _send_responses(self):
        pass

    def _set_pv(self, name, value):
        pass
