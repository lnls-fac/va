
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
                cmd, data = pipe.recv()
                if cmd == 's':
                    name, value = data
                    self.setParam(name, value)
                elif cmd == 'p':
                    prefix, function, args_dict = data
                    self.send_to_model(prefix, function, args_dict)
                else:
                    print('Invalid command:', cmd)

    def read(self, reason):
        utils.log('read', reason, c='yellow')
        return super().read(reason)

    def write(self, reason, value):
        for process in self._processes:
            if reason.startswith(process.model.prefix):
                if reason in process.model.pv_module.get_read_only_pvs() + \
                    process.model.pv_module.get_dynamical_pvs():
                    utils.log('!write', reason, c='yellow', a=['bold'])
                else:
                    utils.log('write', reason + ' ' + str(value), c='yellow', a=['bold'])
                    self.setParam(reason, value)
                    process.pipe.send(('s',(reason, value)))
                break
        else:
            print('Could not find matching system:', reason)

    def send_to_model(self, prefix, function, args_dict):
        for process in self._processes:
            if prefix == process.model.prefix:
                process.pipe.send(('p',(function, args_dict)))
                break
        else:
            print('Could not find matching system:', prefix)
