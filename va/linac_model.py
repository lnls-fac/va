
from . import accelerator_model
from . import beam_charge
from . import utils


class LinacModel(accelerator_model.AcceleratorModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Send value of LITI-EGUN-DELAY to SI
        self._send_queue.put(('g', ('SI', 'LITI-EGUN-DELAY')))

    # --- methods implementing response of model to get requests

    def _get_pv_fake(self, pv_name):
        if 'MODE' in pv_name:
            return self._single_bunch_mode

    def _get_pv_timing(self, pv_name):
        if 'TI-' in pv_name:
            if 'CYCLE' in pv_name:
                return self._ti_cycle
            elif 'EGUN-ENABLED' in pv_name:
                return self._ti_egun_enabled
            elif 'EGUN-DELAY' in pv_name:
                return self._ti_egun_delay
            else:
                return None
        else:
            return None

    # --- methods implementing response of model to set requests

    def _set_pv_fake(self, pv_name, value):
        if 'MODE' in pv_name:
            self._single_bunch_mode = value
            return True
        return False

    def _set_pv_timing(self, pv_name, value):
        if 'CYCLE' in pv_name:
            self._cycle = value
            self._send_queue.put(('s', (pv_name, 0)))
            self._start_injection_cycle()
            self._set_delay_next_cycle()
            self._cycle = 0
            return True
        elif 'TI-EGUN-ENABLED' in pv_name:
            self._ti_egun_enabled = value
            self._state_deprecated = True
            return True
        elif 'TI-EGUN-DELAY' in pv_name:
            self._ti_egun_delay = value
            self._send_queue.put(('g', ('SI', 'LITI-EGUN-DELAY')))
            self._state_deprecated = True
            return True
        return False

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        pass

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._accelerator = self.model_module.create_accelerator()
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)
        self._set_vacuum_chamber(indices='open')
        # Initial values of timing pvs
        self._ti_cycle = 0
        self._ti_egun_enabled = 1
        self._ti_egun_delay = 0
        # Send parameters to TB to start injection efficiency calculations
        self._send_parameters_to_downstream_accelerator({'emittance': self._emittance, 'energy_spread': self._energy_spread,
            'global_coupling': self._global_coupling, 'init_twiss': self._twiss_at_exit})
        self._state_deprecated = True
        self._update_state()

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        if self._beam_charge: self._beam_charge.dump()
        self._orbit = None
        self._twiss = None
        self._si_rf_frequency = None
        self._injection_loss_fraction = 0.0
        self._ejection_loss_fraction = 0.0

    # --- auxilliary methods

    def _start_injection_cycle(self):
        if not self._cycle: return

        self._log(message1='cycle', message2='Starting injection')
        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        if self._single_bunch_mode:
            charge = [self.model_module.single_bunch_charge]
        else:
            charge = [self.model_module.multi_bunch_charge/self.nr_bunches]*self.nr_bunches
        self._log(message1 = 'cycle', message2 = 'electron gun providing charge: {0:.5f} nC'.format(sum(charge)*1e9))

        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))
        self._beam_inject(charge=charge)
        final_charge, _ = self._beam_eject()
        self._send_charge_to_downstream_accelerator({'charge' : final_charge})

    def _receive_pv_value(self, pv_name, value):
        if 'SIRF-FREQUENCY' in pv_name:
            self._si_rf_frequency = value

    def _set_delay_next_cycle(self):
        if self._si_rf_frequency is None: return
        nr_bunches = 1 if self._single_bunch_mode else self.nr_bunches
        self._ti_egun_delay += (1.0/ self._si_rf_frequency) * nr_bunches
        # Set new value of LITI-EGUN-DELAY in epics memory
        self._send_queue.put(('s', ('LITI-EGUN-DELAY', self._ti_egun_delay)))
        # Send new value of LITI-EGUN-DELAY to SI
        self._send_queue.put(('g', ('SI', 'LITI-EGUN-DELAY')))
        self._state_deprecated = True
