
import time
import threading
from pcaspy import Driver
from . import utils


PREFIX_LEN = 2


class DriverThread(threading.Thread):

    def __init__(self, driver, interval, stop_event):
        self._driver = driver
        self._interval = interval
        self._stop_event = stop_event
        super().__init__(target=self._main)

    def _main(self):
        while not self._stop_event.is_set():
            utils.process_and_wait_interval(
                self._driver.process,
                self._interval
            )


class PCASDriver(Driver):

    def  __init__(self, processes, interval):
        super().__init__()
        self._interval = interval
        self._processes = dict()
        for p in processes:
            self._processes[p.model_prefix] = p

    # ***** Break into lower level functions? *****
    def process(self):
        has_pv_changed = False
        for process in self._processes.values():
            pipe = process.pipe
            while pipe.poll():
                request = pipe.recv()
                print(request)
                has_pv_changed |= self._process_request(request)

        if has_pv_changed:
            self.updatePVs()

    def _process_request(self, request):
        # ***** Should functions take data or its elements as input? *****
        cmd, data = request
        if cmd == 's':
            return self._set_parameter_in_memory(data)
        elif cmd == 'g':
            return self._send_parameter_to_model(data)
        elif cmd == 'p':
            return self._call_model_function(data)
        elif cmd == 'sp':
            return self._set_sp_parameters_in_memory(data)
        else:
            utils.log('!cmd', cmd, c='red', a=['bold'])

    def _set_parameter_in_memory(self, data):
        pv_name, value = data
        self.setParam(pv_name, value)
        return True

    def _send_parameter_to_model(self, data):
        prefix, pv_name = data
        value = self.getParam(pv_name)
        self._send_to_model(cmd, prefix, pv_name, value)
        return False

    def _call_model_function(self, data):
        prefix, function, args_dict = data
        self._send_to_model(cmd, prefix, function, args_dict)
        return False

    def _set_sp_parameters_in_memory(self, data):
        sp_pv_list = data
        for pv_name, value in sp_pv_list:
            self.setParam(pv_name, value)
        return True

    def _send_to_model(self, cmd, prefix, *args):
        try:
            process = self._processes[prefix]
            process.pipe.send((cmd, (args)))
        except:
            utils.log('!pref', prefix, c='red', a=['bold'])

    def read(self, reason):
        utils.log('read', reason, c='yellow')
        return super().read(reason)

    def write(self, reason, value):
        try:
            prefix = reason[:PREFIX_LEN]
            process = self._processes[prefix]

            # ***** Move to separate function *****
            if reason in process.model.pv_module.get_read_only_pvs() + \
                    process.model.pv_module.get_dynamical_pvs():
                utils.log('!write', reason, c='yellow', a=['bold'])
            else:
                msg = reason + ' ' + str(value)
                utils.log('write', msg, c='yellow', a=['bold'])
                self.setParam(reason, value)
                self.updatePVs()
                process.pipe.send(('s', (reason, value)))
        except:
            utils.log('!write', reason, c='red', a=['bold'])
