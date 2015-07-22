
from . import accelerator_model
from . import utils


class TLineModel(accelerator_model.AcceleratorModel):

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._state_deprecated or self._upstream_accelerator_state_deprecated:
            self._state_deprecated = False
            self._upstream_accelerator_state_deprecated = False
            self._injection_loss_fraction = 0.0
            self._calc_transport_loss_fraction()
            self._ejection_loss_fraction  = 0.0

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        super()._beam_dump(message1=message1, message2=message2, c=c, a=a)
        self._injection_parameters = None
        self._transport_loss_fraction = None

    # --- auxilliary methods

    def _beam_transport(self):
        efficiency = 1.0 - self._transport_loss_fraction
        final_charge = self._beam_charge.value
        self._log(message1='cycle', message2='beam transport at {0:s}: {1:.2f}% efficiency'.format(self.model_module.lattice_version, 100*efficiency))
        return final_charge

    def _calc_transport_loss_fraction(self):
        if self.prefix == 'LI':
            self._transport_loss_fraction = 0.0
            parameters = {'emittance': self._emittance, 'energy_spread': self._energy_spread, 'global_coupling': self._global_coupling}
            self._send_parameters_to_downstream_accelerator(self._twiss_at_exit, parameters)
        else:
            if self._injection_parameters is None: return
            self._log('calc', 'transport efficiency  for '+self.model_module.lattice_version)

            args_dict = self._injection_parameters
            args_dict.update(self._get_geometrical_parameters())
            self._transport_loss_fraction, self._twiss, self._m66, self._transfer_matrices, self._orbit = \
                utils.charge_loss_fraction_line(self._accelerator, **args_dict)
            self._send_parameters_to_downstream_accelerator(self._twiss[-1], self._injection_parameters)
