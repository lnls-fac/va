
import queue
import numpy
from pcaspy import Driver
import va.li_pvs as li_pvs
import va.tb_pvs as tb_pvs
import va.bo_pvs as bo_pvs
import va.ts_pvs as ts_pvs
import va.si_pvs as si_pvs
import va.ti_pvs as ti_pvs
import utils


class PCASDriver(Driver):

    def  __init__(self, li_model = None,
                        tb_model = None,
                        bo_model = None,
                        ts_model = None,
                        si_model = None,
                        ti_model = None):

        super().__init__()

        # subsystems
        self.li_model = li_model   # linac
        self.tb_model = tb_model   # linac-to-booster transport line
        self.bo_model = bo_model   # booster
        self.ts_model = ts_model   # booster-to-storage ring transport line
        self.si_model = si_model   # storage ring
        self.ti_model = ti_model   # timing

        self.queue = queue.Queue()
        self.li_deprecated = True
        self.tb_deprecated = True
        self.bo_deprecated = True
        self.ts_deprecated = True
        self.si_deprecated = True
        self.ti_deprecated = True

        # signals models of sybsystem what driver object is using them
        if self.li_model: self.li_model._driver = self
        if self.tb_model: self.tb_model._driver = self
        if self.bo_model: self.bo_model._driver = self
        if self.ts_model: self.ts_model._driver = self
        if self.si_model: self.si_model._driver = self
        if self.ti_model: self.ti_model._driver = self

        self.read_only_pvs  = li_pvs.read_only_pvs + \
                              tb_pvs.read_only_pvs +\
                              bo_pvs.read_only_pvs + \
                              ts_pvs.read_only_pvs + \
                              si_pvs.read_only_pvs + \
                              ti_pvs.read_only_pvs
        self.read_write_pvs = li_pvs.read_write_pvs + \
                              tb_pvs.read_write_pvs + \
                              bo_pvs.read_write_pvs + \
                              ts_pvs.read_write_pvs + \
                              si_pvs.read_write_pvs + \
                              ti_pvs.read_write_pvs
        self.dynamic_pvs    = li_pvs.dynamic_pvs + \
                              tb_pvs.dynamic_pvs + \
                              bo_pvs.dynamic_pvs + \
                              ts_pvs.dynamic_pvs + \
                              si_pvs.dynamic_pvs + \
                              ti_pvs.dynamic_pvs

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

        self.li_deprecated = False
        self.tb_deprecated = False
        self.bo_deprecated = False
        self.ts_deprecated = False
        self.si_deprecated = False
        self.ti_deprecated = False

    def set_model_parameter(self, pv_name, value):
        """Set model parameter in physical units."""

        if pv_name.startswith('LI'):
            self.li_deprecated = True
            self.li_model.set_pv(pv_name, value)
        elif pv_name.startswith('TB'):
            self.tb_deprecated = True
            self.tb_model.set_pv(pv_name, value)
        elif pv_name.startswith('BO'):
            self.bo_deprecated = True
            self.bo_model.set_pv(pv_name, value)
        elif pv_name.startswith('TS'):
            self.ts_deprecated = True
            self.ts_model.set_pv(pv_name, value)
        elif pv_name.startswith('SI'):
            self.si_deprecated = True
            self.si_model.set_pv(pv_name, value)
        elif pv_name.startswith('TI'):
            self.ti_deprecated = True
            self.ti_model.set_pv(pv_name, value)
        else:
            raise Exception('subsystem not found')

    def update_model_state(self):
        self.li_model.update_state()
        self.tb_model.update_state()
        self.bo_model.update_state()
        self.ts_model.update_state()
        self.si_model.update_state()
        self.ti_model.update_state()

    def update_epics_from_model(self):

        # linac
        if self.li_deprecated:
            for pv in li_pvs.read_only_pvs:
                value = self.li_model.get_pv(pv)
                self.setParam(pv, value)
        else:
            for pv in li_pvs.dynamic_pvs:
                value = self.li_model.get_pv(pv)
                self.setParam(pv, value)

        # linac-to-booster transport line
        if self.tb_deprecated:
            for pv in tb_pvs.read_only_pvs:
                value = self.tb_model.get_pv(pv)
                self.setParam(pv, value)
        else:
            for pv in tb_pvs.dynamic_pvs:
                value = self.tb_model.get_pv(pv)
                self.setParam(pv, value)

        # booster
        if self.bo_deprecated:
            for pv in bo_pvs.read_only_pvs:
                value = self.bo_model.get_pv(pv)
                self.setParam(pv, value)
        else:
            for pv in bo_pvs.dynamic_pvs:
                value = self.bo_model.get_pv(pv)
                self.setParam(pv, value)

        # booster-to-storage ring transport line
        if self.ts_deprecated:
            for pv in ts_pvs.read_only_pvs:
                value = self.ts_model.get_pv(pv)
                self.setParam(pv, value)
        else:
            for pv in ts_pvs.dynamic_pvs:
                value = self.ts_model.get_pv(pv)
                self.setParam(pv, value)

        # sirius
        if self.si_deprecated:
            for pv in si_pvs.read_only_pvs:
                value = self.si_model.get_pv(pv)
                self.setParam(pv, value)
        else:
            for pv in si_pvs.dynamic_pvs:
                value = self.si_model.get_pv(pv)
                self.setParam(pv, value)

        # timing
        if self.ti_deprecated:
            for pv in ti_pvs.read_only_pvs:
                value = self.ti_model.get_pv(pv)
                self.setParam(pv, value)
        else:
            for pv in ti_pvs.dynamic_pvs:
                value = self.ti_model.get_pv(pv)
                self.setParam(pv, value)

    def update_sp_pv_values(self):
        utils.log('init', 'epics sp memory for LI pvs')
        for pv in li_pvs.read_write_pvs:
            value = self.li_model.get_pv(pv)
            self.setParam(pv, value)

        utils.log('init', 'epics sp memory for TB pvs')
        for pv in tb_pvs.read_write_pvs:
            value = self.tb_model.get_pv(pv)
            self.setParam(pv, value)

        utils.log('init', 'epics sp memory for BO pvs')
        for pv in bo_pvs.read_write_pvs:
            value = self.bo_model.get_pv(pv)
            self.setParam(pv, value)

        utils.log('init', 'epics sp memory for TS pvs')
        for pv in ts_pvs.read_write_pvs:
            value = self.ts_model.get_pv(pv)
            self.setParam(pv, value)

        utils.log('init', 'epics sp memory for SI pvs')
        for pv in si_pvs.read_write_pvs:
            value = self.si_model.get_pv(pv)
            self.setParam(pv, value)

        utils.log('init', 'epics sp memory for TI pvs')
        for pv in ti_pvs.read_write_pvs:
            value = self.ti_model.get_pv(pv)
            self.setParam(pv, value)
