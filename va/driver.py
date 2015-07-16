
import time
import threading
from pcaspy import Driver
from . import utils


class DriverThread(threading.Thread):

    def __init__(self, driver, interval, stop_event):
        self._driver = driver
        self._interval = interval
        self._stop_event = stop_event
        super().__init__(target=self._main)

    def _main(self):
        while not self._stop_event.is_set():
            utils.process_and_wait_interval(self._driver.process,
                self._interval)


class PCASDriver(Driver):

    def  __init__(self, processes):
        super().__init__()
        self._processes = processes

    def process(self):
        for process in self._processes:
            pipe = process.pipe
            while pipe.poll():
                cmd, name, value = pipe.recv()
                if cmd == 'p':
                    self.write(name, value)
                elif cmd == 's':
                    self.setParam(name, value)
                else:
                    print('Invalid command:', cmd)

    def read(self, reason):
        utils.log('read', reason, c='yellow')
        return super().read(reason)

    def write(self, reason, value):
        for process in self._processes:
            if reason.startswith(process.model.prefix):
                self.setParam(reason, value)
                process.pipe.send((reason, value))
                break
        else:
            print('Could not find matching system:', reason)
