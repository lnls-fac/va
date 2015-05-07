
import queue
import numpy
from pcaspy import Driver
import va.si_pvs as si_pvs
import va.bo_pvs as bo_pvs
import exccurve
import utils


class PCASDriver(Driver):

    def  __init__(self, si_model = None,
                        bo_model = None,
                        ts_model = None,
                        tb_model = None,
                        li_model = None):
        super().__init__()
        self.si_model = si_model
        self.bo_model = bo_model
        self.ts_model = ts_model
        self.tb_model = tb_model
        self.li_model = li_model
        self.queue = queue.Queue()

        self.read_only_pvs  = si_pvs.read_only_pvs + bo_pvs.read_only_pvs
        self.read_write_pvs = si_pvs.read_write_pvs + bo_pvs.read_write_pvs

    def read(self, reason):
        print(utils.timestamp_message('read  ' + reason))
        return super().read(reason)

    def write(self, reason, value):
        if reason in self.read_only_pvs:
            print(utils.timestamp_message('!!! write ' + reason + ' ' + str(value), a2=['bold']))
        else:
            print(utils.timestamp_message('write ' + reason + ' ' + str(value), a2=['bold']))
            self.queue.put((reason, value))
            self.setParam(reason, value)

    def update_pvs(self):
        """Update model PVs, recalculate changed parameters and read them back.
        """
        for i in range(self.queue.qsize()):
            pv_name, value = self.queue.get()
            if pv_name in self.read_only_pvs:
                continue
            self.set_model_parameter(pv_name, value)

        self.update_model_state()
        self.update_pv_values()

        self.updatePVs()

    def set_model_parameter(self, pv_name, value):
        """Set model parameter in physical units."""

        if pv_name.startswith('SI'):
            self.si_model.set_pv(pv_name, value)
        elif pv_name.startswith('BO'):
            self.bo_model.set_pv(pv_name, value)
        elif pv_name.startswith('TS'):
            raise Exception('TS model not implemented yet')
        elif pv_name.startswith('TB'):
            raise Exception('TB model not implemented yet')
        elif pv_name.startswith('LI'):
            raise Exception('LI model not implemented yet')
        else:
            raise Exception('subsystem not found')

    def update_model_state(self):
        if self.si_model:
            self.si_model.update_state()
        if self.bo_model:
            self.bo_model.update_state()

    def update_pv_values(self):
        for pv in si_pvs.read_only_pvs:
            if self.si_model:
                value = self.si_model.get_pv(pv)
                self.setParam(pv, value)
        for pv in bo_pvs.read_only_pvs:
            if self.bo_model:
                value = self.bo_model.get_pv(pv)
                self.setParam(pv, self.bo_model.get_pv(pv))

    def update_sp_pv_values(self):
        for pv in si_pvs.read_write_pvs:
            value = self.si_model.get_pv(pv)
            self.setParam(pv, value)
