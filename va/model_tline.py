
import numpy
import pyaccel
import va.utils as utils
from va.model_accelerator import AcceleratorModel, UNDEF_VALUE

class TLineModel(AcceleratorModel):

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(all_pvs=all_pvs, log_func=log_func)

    # --- methods that help updating the model state

    def update_state(self, force=False):
        if force:
            self._calc_transport_loss_fraction()
            self._state_deprecated = False
            self._upstream_accelerator_state_deprecated = False
            self._notify_driver()
        elif self._state_deprecated or self._upstream_accelerator_state_deprecated:
            self._calc_transport_loss_fraction()
            self._state_deprecated = False
            self._upstream_accelerator_state_deprecated = False
            # signaling deprecation for other models
            if self._prefix=='LI':
                self._driver.tb_model._upstream_accelerator_state_deprecated = True
            elif self._prefix=='TB':
                self._driver.bo_model._upstream_accelerator_state_deprecated = True
            self._notify_driver()

    def beam_transport(self, charge):
        self.update_state()
        self._beam_charge.inject(charge)
        efficiency = 1.0 - self._transport_loss_fraction
        final_charge = numpy.multiply(charge, efficiency)
        self._beam_charge.dump()
        return final_charge, efficiency

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        super()._beam_dump(message1=message1, message2=message2, c=c, a=a)
        self._transport_loss_fraction = None

    # --- auxilliary methods

    def _calc_transport_loss_fraction(self):
        if self._model_module.lattice_version.startswith('LI'):
            self._transport_loss_fraction = 0.0
        else:
            self._log('calc', 'transport efficiency  for '+self._prefix)
            args_dict = self._get_parameters_from_upstream_accelerator()
            args_dict.update(self._get_vacuum_chamber())
            args_dict.update(self._get_coordinate_system_parameters())
            self._transport_loss_fraction, self._twiss, self._m66, self._transfer_matrices, self._orbit = \
                utils.charge_loss_fraction_line(self._accelerator, **args_dict)
