
"""Accelerator model module

The Model class in this module is in charge of the initialisation and
interaction with the engine (pyaccel/trackcpp). It updates values and
recalculates necessary parameters, controlling concurrent accesses coming from
the server.
"""

import mathphys
import va.utils as utils

TRACK6D     = False
VCHAMBER    = False
UNDEF_VALUE = 0.0
_u = mathphys.units


#--- general model classes ---#

class Model(object):

    def __init__(self, all_pvs=None, log_func=utils.log):
        # stored model state parameters
        self._driver = None # this will be set latter by Driver
        self._log = log_func
        self._all_pvs = all_pvs

    # --- methods that help updating the model state

    def get_pv(self, pv_name):
        pass

    def set_pv(self, pv_name, value):
        pass

    def update_state(self, force=False):
        pass

    def all_models_defined_ack(self):
        self.update_state(force=True)
