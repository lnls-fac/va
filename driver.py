
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
                        li_model = None,
                        sy_model = None):

        super().__init__()
        self.si_model = si_model   # storage ring
        self.bo_model = bo_model   # booster
        self.ts_model = ts_model   # booster-to-storage ring transport line
        self.tb_model = tb_model   # linac-to-booster transport line
        self.li_model = li_model   # linac
        self.sy_model = sy_model   # synchronism
        self.queue = queue.Queue()
        self.si_deprecated = True
        self.bo_deprecated = True

        # signals models of sybsystem what driver object is using them
        if self.si_model: self.si_model._driver = self
        if self.bo_model: self.bo_model._driver = self
        if self.ts_model: self.ts_model._driver = self
        if self.tb_model: self.tb_model._driver = self
        if self.li_model: self.li_model._driver = self

        self.read_only_pvs  = si_pvs.read_only_pvs + bo_pvs.read_only_pvs
        self.read_write_pvs = si_pvs.read_write_pvs + bo_pvs.read_write_pvs
        self.dynamic_pvs    = si_pvs.dynamic_pvs + bo_pvs.dynamic_pvs

    def read(self, reason):
        utils.log('read',reason,c='yellow')
        return super().read(reason)

    def write(self, reason, value):
        if reason in self.read_only_pvs:
            utils.log('!write',reason + ' ' + str(value), c='yellow', a=['bold'])
        else:
            utils.log('write', reason + ' ' + str(value), c='yellow', a=['bold'])
            self.queue.put((reason, value))
            self.setParam(reason, value)

    def update_pvs(self):
        """Update model PVs, recalculate changed parameters and read them back.
        """

        # first process all write requests
        for i in range(self.queue.qsize()):
            pv_name, value = self.queue.get()
            self.set_model_parameter(pv_name, value)

        # then update model states and epics memory
        self.update_model_state()
        self.update_epics_from_model()
        self.updatePVs()

        self.si_deprecated = False
        self.bo_deprecated = False

    def set_model_parameter(self, pv_name, value):
        """Set model parameter in physical units."""

        if pv_name.startswith('SI'):
            self.si_deprecated = True
            self.si_model.set_pv(pv_name, value)
        elif pv_name.startswith('BO'):
            self.bo_deprecated = True
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

        #print(utils.timestamp_message('update', 'model state of SI', c2='yellow'))
        self.si_model.update_state()

        #print(utils.timestamp_message('update', 'model state of BO', c2='yellow'))
        self.bo_model.update_state()

    def update_epics_from_model(self):

        #print(utils.timestamp_message('update', 'EPICS pv values in memory from SI', c2='yellow'))
        if self.si_deprecated:
            for pv in si_pvs.read_only_pvs:
                value = self.si_model.get_pv(pv)
                self.setParam(pv, value)
        else:
            for pv in si_pvs.dynamic_pvs:
                value = self.si_model.get_pv(pv)
                self.setParam(pv, value)

        #print(utils.timestamp_message('update', 'EPICS pv values in memory from BO', c2='yellow'))
        if self.bo_deprecated:
            for pv in bo_pvs.read_only_pvs:
                value = self.bo_model.get_pv(pv)
                self.setParam(pv, value)
        else:
            for pv in bo_pvs.dynamic_pvs:
                value = self.bo_model.get_pv(pv)
                self.setParam(pv, value)

    def update_sp_pv_values(self):
        utils.log('init', 'epics sp memory for SI pvs')
        for pv in si_pvs.read_write_pvs:
            value = self.si_model.get_pv(pv)
            self.setParam(pv, value)
        utils.log('init', 'epics sp memory for BO pvs')
        for pv in bo_pvs.read_write_pvs:
            value = self.bo_model.get_pv(pv)
            self.setParam(pv, value)
