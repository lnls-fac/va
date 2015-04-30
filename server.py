#!/usr/bin/env python3

import time
import signal
import threading
from pcaspy import Driver, SimpleServer
import va.model as models
import va.pv_names as pv_names


class PCASDriver(Driver):
    def  __init__(self, si_model):
        super().__init__()
        self.si_model = si_model

    def read(self, reason):
        print(reason)
        if reason.startswith('SI'):
            value = self.si_model.get_pv(reason)
        else:
            raise Exception('model not implemented')

        return value

    def write(self, reason, value):
        if reason.startswith('SI'):
            model = self.si_model
        else:
            raise Exception('model not implemented')

        model.set_pv(reason, value)


class ModelThread(threading.Thread):

    def __init__(self, model):
        self._model = model
        super().__init__(target=self._main)

    def stop(self):
        self._model.stop()
        self.join()
        return self.is_alive()

    def _main(self):
        self._model.process()


def handler(signum, frame):
    global si_thread
    global is_running
    print('Received signal', signum)
    print('Active thread count:', threading.active_count())
    print('Is alive?', si_thread.stop())
    is_running = False


if __name__ == '__main__':

    signal.signal(signal.SIGINT, handler)

    si = models.SiModel()

    si_thread = ModelThread(si)
    si_thread.start()


    pvdb = {}
    for key in pv_names.bpm.keys():
        pvdb['SI'+key] = {'type' : 'float', 'count': 2}

    server = SimpleServer()
    server.createPV('', pvdb)
    driver = PCASDriver(si)

    is_running = True
    while is_running:
        server.process(0.1)
