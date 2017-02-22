
import multiprocessing
import time
from . import utils


class AreaStructureProcess(multiprocessing.Process):

    def __init__(self, area_structure, interval, stop_event, finalisation):
        """Initialise, start and manage area_structure and area_structure processing.

        Keyword arguments: see start_and_run_area_structure
        """
        send_queue = multiprocessing.Queue()
        recv_queue = multiprocessing.Queue()
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.area_structure = area_structure
        self.area_structure_prefix = area_structure.prefix

        super().__init__(
            target=start_and_run_area_structure,
            kwargs={
                'area_structure': area_structure,
                'interval': interval,
                'stop_event': stop_event,
                # Queues are supposed to be exchanged
                'send_queue': recv_queue,
                'recv_queue': send_queue,
                'finalisation': finalisation,
            }
        )


def start_and_run_area_structure(area_structure, interval, stop_event, finalisation, **kwargs):
    """Start periodic processing of area_structure

    Keyword arguments:
    area_structure -- area_structure class
    interval -- processing interval [s]
    stop_event -- event to stop processing
    finalisation -- barrier to wait before finalisation
    **kwargs -- extra arguments to area_structure __init__
    """
    As = area_structure(**kwargs)
    while not stop_event.is_set():
        utils.process_and_wait_interval(As.process, interval)
    else:
        finalisation.wait()
        As.empty_queues()
        finalisation.wait()
        As.finalise()


class AreaStructure:

    def __init__(self, send_queue, recv_queue, log_func=utils.log, **kwargs):
        self._send_queue = send_queue
        self._recv_queue = recv_queue
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
        elif cmd == 'p':
            self._get_parameters_from_other_area_structure(data)
        else:
            utils.log('!cmd', cmd, c='red', a=['bold'])

    def _update_state(self):
        return 1

    def _set_parameter(self, data):
        pv_name, value = data
        self._set_pv(pv_name, value)

    def _update_pvs(self):
        pvs = self.pv_module.get_dynamical_pvs()
        pvs = pvs + (self.pv_module.get_read_only_pvs() if self._state_changed else [])
        for pv in pvs:
            self._send_queue.put(('s', (pv, self._get_pv(pv))))
        self._state_changed = False

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
        utils.log('exit', 'area_structure ' + self.prefix)

    def _send_parameters_to_other_area_structure(self, prefix, _dict):
        self._send_queue.put(('p', (prefix, _dict)))

    def _get_parameters_from_other_area_structure(self, _dict):
        if 'pulsed_magnet_parameters' in _dict.keys():
            self._set_pulsed_magnets_parameters(**_dict['pulsed_magnet_parameters'])
        elif 'update_delays' in _dict.keys():
            self._update_pulsed_magnets_delays(_dict['update_delays'])
        elif 'injection_parameters' in _dict.keys():
            self._injection_parameters = _dict['injection_parameters']
            self._update_injection_efficiency = True
        elif 'injection_cycle' in _dict.keys():
            # self._received_charge = True
            self._update_state()
            self._injection_cycle(**_dict['injection_cycle'])
            # self._received_charge = False

    def _init_sp_pv_values(self):
        utils.log('init', 'epics sp memory for %s pvs'%self.prefix)
        sp_pv_list = []
        for pv in self.pv_module.get_read_write_pvs() + self.pv_module.get_constant_pvs():
            value = self._get_pv(pv)
            sp_pv_list.append((pv,value))
        self._send_queue.put(('sp', sp_pv_list ))
