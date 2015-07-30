
import time
from .accelerator_model import AcceleratorModel
from . import utils

class TLineModel(AcceleratorModel):

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
        charge = self._beam_charge.value
        final_charge = [charge_bunch * efficiency for charge_bunch in charge]
        self._beam_charge.dump()
        self._beam_charge.inject(final_charge)
        return efficiency

    def _calc_transport_loss_fraction(self):
        t0 = time.time()
        if self._injection_parameters is None: return
        self._log('calc', 'transport efficiency  for '+self.model_module.lattice_version)
        args_dict = {}
        args_dict.update(self._injection_parameters)
        args_dict.update(self._get_vacuum_chamber())
        args_dict.update(self._get_coordinate_system_parameters())
        self._transport_loss_fraction, self._twiss, self._m66, self._transfer_matrices, self._orbit = \
            utils.charge_loss_fraction_line(self._accelerator, **args_dict)
        self._send_parameters_to_downstream_accelerator(self._twiss[-1], self._injection_parameters)

    def _get_charge_from_upstream_accelerator(self, charge=None):
        if charge is None: return
        t0 = time.time()
        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))
        self._beam_inject(charge=charge)
        efficiency = self._beam_transport()
        self._log(message1='cycle', message2='beam transport at {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*efficiency))
        final_charge, _ = self._beam_eject()
        self._send_charge_to_downstream_accelerator(final_charge)
