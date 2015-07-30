
from .tline_model import TLineModel
import time

class LinacModel(TLineModel):

    # --- methods implementing response of model to get requests

    def _get_pv_static(self, pv_name):
        if 'MODE' in pv_name:
            return self._single_bunch_mode

  # --- methods implementing response of model to set requests

    def _set_pv_control(self, pv_name, value):
        if 'MODE' in pv_name:
            self._single_bunch_mode = value
            self._pipe.send(('g', ('TI', 'LI-CO-MODE')))
            return True
        return False

   # --- auxilliary methods

    def _calc_transport_loss_fraction(self):
        self._transport_loss_fraction = 0.0
        parameters = {'emittance': self._emittance, 'energy_spread': self._energy_spread, 'global_coupling': self._global_coupling}
        self._send_parameters_to_downstream_accelerator(self._twiss_at_exit, parameters)

    def _receive_synchronism_signal(self):
        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        if self._single_bunch_mode:
            charge = [self.model_module.single_bunch_charge]
        else:
            charge = [self.model_module.multi_bunch_charge/self.nr_bunches]*self.nr_bunches
        self._log(message1 = 'cycle', message2 = 'electron gun providing charge: {0:.5f} nC'.format(sum(charge)*1e9))
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))
        self._beam_inject(charge=charge)
        efficiency = self._beam_transport()
        self._log(message1='cycle', message2='beam transport at {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*efficiency))
        final_charge, _ = self._beam_eject()
        self._send_charge_to_downstream_accelerator(final_charge)
