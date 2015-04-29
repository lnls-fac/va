
import time
import signal
import threading
import va.model as model


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
    global t
    print('Received signal', signum)
    print('Active thread count:', threading.active_count())
    print('Is alive?', t.stop())


if __name__ == '__main__':

    signal.signal(signal.SIGINT, handler)

    si = model.SiModel()

    t = ModelThread(si)
    t.start()

    si.set_pv('A1', 1.0)
    si.set_pv('A2', 2.1)
    time.sleep(0.5)
    si._queue.put('B')
