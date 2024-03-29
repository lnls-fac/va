import uuid as _uuid
import multiprocessing
from va import utils
import traceback
import sys
# import prctl #Used in debugging

SIMUL_ONLY_ORBIT = False

class AreaStructureProcess(multiprocessing.Process):

    def __init__(self, area_structure_cls, interval, stop_event, finalisation):
        """Initialize, start and manage area_structure and area_structure processing.

        Keyword arguments: see start_and_run_area_structure
        """
        my_queue = multiprocessing.Queue()
        self.others_queue = dict()
        self.my_queue = my_queue
        self.area_structure_cls = area_structure_cls
        self.area_structure_prefix = area_structure_cls.prefix

        super().__init__(
            target=self.start_and_run_area_structure,
            kwargs={
                'area_structure_cls': area_structure_cls,
                'interval': interval,
                'stop_event': stop_event,
                # Queues are supposed to be exchanged
                'others_queue': self.others_queue,
                'my_queue': my_queue,
                'finalisation': finalisation,
                },
            name = 'Thread-' + area_structure_cls.prefix
            )

    def set_others_queue(self, queues):
        for prefix, queue in queues.items():
            if prefix == self.area_structure_prefix:
                continue
            self.others_queue[prefix] = queue

    def start_and_run_area_structure(self, area_structure_cls, interval, stop_event, finalisation, **kwargs):
        """Start periodic processing of area_structure

        Keyword arguments:
        area_structure_cls -- area_structure class
        interval -- processing interval [s]
        stop_event -- event to stop processing
        finalization -- barrier to wait before finalization
        **kwargs -- extra arguments to area_structure __init__
        """
        area_structure = area_structure_cls(**kwargs)
        # prctl.set_name(self.name) # For debug

        try:
            while not stop_event.is_set():
                utils.process_and_wait_interval(area_structure.process, interval)
        except Exception as ex:
            exc_info = sys.exc_info()
            print('--- traceback ---')
            traceback.print_exception(*exc_info)
            del exc_info
            print('-----------------')
            utils.log('error2', str(ex), 'red')
            stop_event.set()
        finally:
            area_structure.close_others_queues()
            finalisation.wait()
            area_structure.empty_my_queue()
            finalisation.wait()
            area_structure.finalise()


class AreaStructure:

    def __init__(self, others_queue, my_queue, log_func=utils.log, **kwargs):
        self._uuid = _uuid.uuid4()
        self._others_queue = others_queue
        self._my_queue = my_queue
        self._log = log_func
        self._state_changed = False
        self.simulate_only_orbit = SIMUL_ONLY_ORBIT

    @property
    def log(self):
        """."""
        return self._log
        
    def process(self):
        self._process_requests()
        self._update_state()
        self._update_pvs()

    def _process_requests(self):
        size = self._my_queue.qsize()
        for _ in range(size):
            request = self._my_queue.get()
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
        pvs = []

        # update dynamical PVs (if not simulating only orbit)
        if not self.simulate_only_orbit:
            pvs = pvs + self.pv_module.get_dynamical_pvs()

        # if model changes, also update all read-only PVs
        # NOTE: this can be improved. instead of sending all read_only_pvs to drive
        # one can keep a list of changed PVs.
        pvs = pvs + (self.pv_module.get_read_only_pvs() if self._state_changed else [])
        for pv in pvs:
            self._others_queue['driver'].put(('s', (pv, self._get_pv(pv))))

        # signal that model state change has already been propagated to epics driver
        self._state_changed = False

    def close_others_queues(self):
        for q in self._others_queue.values():
            q.close()

    def empty_my_queue(self):
        while not self._my_queue.empty():
            self._my_queue.get()

    def finalise(self):
        self._my_queue.close()
        self._my_queue.join_thread()
        utils.log('exit', 'area_structure ' + self.prefix)

    def _send_parameters_to_other_area_structure(self, prefix, _dict):
        if prefix in self._others_queue:
            # print('{} sending to {}: '.format(self.prefix, prefix), _dict)
            self._others_queue[prefix].put(('p', _dict))

    def _get_parameters_from_other_area_structure(self, _dict):
        # print('{} receiving: '.format(self.prefix), _dict)
        if 'pulsed_magnet_parameters' in _dict.keys():
            self._set_pulsed_magnets_parameters(
                **_dict['pulsed_magnet_parameters'])
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
        utils.log('epics', '{}: setting database for setpoint pvs'.format(
            self.prefix))
        sp_pv_list = []
        for pv in self.pv_module.get_read_write_pvs() + self.pv_module.get_constant_pvs():
            value = self._get_pv(pv)
            sp_pv_list.append((pv, value))
        self._others_queue['driver'].put(('sp', sp_pv_list))

    def _send_initialisation_sign(self):
        self.process()
        self._others_queue['driver'].put(('i', self.prefix))
