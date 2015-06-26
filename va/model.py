
"""Accelerator model module

The Model class in this module is in charge of the initialisation and
interaction with the engine (pyaccel/trackcpp). It updates values and
recalculates necessary parameters, controlling concurrent accesses coming from
the server.
"""

import pyaccel
import va.utils as utils
import mathphys


TRACK6D     = False
VCHAMBER    = False
UNDEF_VALUE = 0.0

_u, _Tp = mathphys.units, pyaccel.optics.get_revolution_period


#--- general model classes ---#

class Model(object):

    def __init__(self, model_module=None, all_pvs=None, log_func=utils.log):
        # stored model state parameters
        self._driver = None # this will be set latter by Driver
        self._model_module = model_module
        self._log = log_func
        self._all_pvs = all_pvs

    # --- methods implementing response of model to get and set requests

    def get_pv(self, pv_name):
        value = self.get_pv_dynamic(pv_name)
        if value is None:
            #print('try static: ' + pv_name + ' ', end='')
            value = self.get_pv_static(pv_name)
            #print(value)
        if value is None:
            #print('try fake: ' + pv_name)
            value = self.get_pv_fake(pv_name)
        if value is None:
            raise Exception('response to ' + pv_name + ' not implemented in model get_pv')
        return value

    def set_pv(self, pv_name, value):
        return None

    def get_pv_dynamic(self, pv_name):
        return None

    def get_pv_static(self, pv_name):
        return None

    def get_pv_fake(self, pv_name):
        return None

    def set_pv_fake(self, pv_name, value):
        if '-ERRORX' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorx = pyaccel.lattice.get_error_misalignment_x(self._accelerator, idx[0])
            if value != prev_errorx:
                pyaccel.lattice.set_error_misalignment_x(self._accelerator, idx, value)
                self._state_deprecated = True
            return True
        elif '-ERRORY' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errory = pyaccel.lattice.get_error_misalignment_y(self._accelerator, idx[0])
            if value != prev_errory:
                pyaccel.lattice.set_error_misalignment_y(self._accelerator, idx, value)
                self._state_deprecated = True
            return True
        elif '-ERRORR' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            prev_errorr = pyaccel.lattice.get_error_rotation_roll(self._accelerator, idx[0])
            if value != prev_errorr:
                pyaccel.lattice.set_error_rotation_roll(self._accelerator, idx, value)
                self._state_deprecated = True
            return True
        return False

    # --- methods that help updating the model state

    def update_state(self, force=False):
        pass

    def all_models_defined_ack(self):
        self.update_state(force=True)

    # --- auxilliary methods

    def _transform_to_local_coordinates(self, old_pos, delta_rx, angle, delta_dl=0.0):
        C, S = math.cos(angle), math.sin(angle)
        old_angle = math.atan(old_pos.px)
        new_pos = [p for p in old_pos]
        new_pos[0] =  C * old_pos[0] + S * old_pos[5]
        new_pos[5] = -S * old_pos[0] + C * old_pos[5]
        new_pos[1] = math.tan(angle + old_angle)
        return new_pos
