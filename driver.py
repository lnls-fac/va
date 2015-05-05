
import queue
import numpy
from pcaspy import Driver
import va.si_pvs as si_pvs
import exccurve


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

        self.read_only_pvs = si_pvs.read_only_pvs
        self.read_write_pvs = si_pvs.read_write_pvs

    def read(self, reason):
        print('read:' + reason)
        return super().read(reason)

    def write(self, reason, value):
        print('write: ' + reason)
        self.queue.put((reason, value))
        self.setParam(reason, value)

    def update_pvs(self):
        """Update model PVs, recalculate changed parameters and read them back.
        """
        for i in range(self.queue.qsize()):
            pv_name, value = self.queue.get()
            if pv_name in self.read_only_pvs:
                continue
            value = self.conv_hw2phys(pv_name, value)
            self.set_model_parameter(pv_name, value)

        self.update_model_state()
        self.update_pv_values()

        self.updatePVs()

    def set_model_parameter(self, pv_name, value):
        """Set model parameter in physical units."""

        if pv_name.startswith('SI'):
            self.si_model.set_pv(pv_name, value)
        elif pv_name.startswith('BO'):
            raise Exception('BO model not implemented yet')
        elif pv_name.startswith('TS'):
            raise Exception('TS model not implemented yet')
        elif pv_name.startswith('TB'):
            raise Exception('TB model not implemented yet')
        elif pv_name.startswith('LI'):
            raise Exception('LI model not implemented yet')
        else:
            raise Exception('subsystem not found')

    def update_model_state(self):
        self.si_model.update_state()
        #self.bo_model.update_state()
        #self.ts_model.update_state()
        #self.tb_model.update_state()
        #self.li_model.update_state()

    def update_pv_values(self):
        for pv in si_pvs.read_only_pvs:
            value = self.si_model.get_pv(pv)
            self.setParam(pv, value)
        # for pv in bo_pvs.read_only_pvs:
        #     self.setParam(pv, self.bo_model.get_pv(pv))
        # for pv in ts_pvs.read_only_pvs:
        #     self.setParam(pv, self.ts_model.get_pv(pv))
        # for pv in tb_pvs.read_only_pvs:
        #     self.setParam(pv, self.tb_model.get_pv(pv))
        # for pv in li_pvs.read_only_pvs:
        #     self.setParam(pv, self.li_model.get_pv(pv))

    def update_sp_pv_values(self):
        for pv in self.read_write_pvs:
            value = self.si_model.get_pv(pv)
            self.setParam(pv, value)

    def conv_hw2phys(self, pv_name, value):
        """Convert PV value from hardware to physical units."""
        if 'PS-CHS' in pv_name:
            return self.conv_current2kick(value)
        elif 'PS-Q' in pv_name:
            return self.conv_current2quad_str(value)
        else:
            return value

    def conv_phys2hw(self, pv_name, value):
        """Convert PV value from physical to hardware units."""
        if 'PS-CHS' in pv_name:
            return self.conv_kick2current(value)
        elif 'PS-Q' in pv_name:
            return self.conv_quad_str2current(value)
        else:
            return value

    def conv_current2kick(self, value):
        return value

    def conv_quad_str2current(self, value):
        return numpy.interp(value, exccurve.k, exccurve.i)

    def conv_kick2current(self, value):
        return value

    def conv_current2quad_str(self, value):
        return numpy.interp(value, exccurve.i, exccurve.k)
