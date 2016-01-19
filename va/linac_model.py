
import pyaccel
from . import accelerator_model
from . import beam_charge
from . import utils

UNDEF_VALUE = accelerator_model.UNDEF_VALUE

class LinacModel(accelerator_model.AcceleratorModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # --- methods implementing response of model to get requests

    def _get_pv_fake(self, pv_name):
        if 'MODE' in pv_name:
            return self._single_bunch_mode
        return super()._get_pv_fake(pv_name)


    def _get_pv_timing(self, pv_name):
        if 'TI-' in pv_name:
            if 'CYCLE' in pv_name:
                return self._cycle
            elif 'EGUN-ENABLED' in pv_name:
                return self._egun_enabled
            elif 'EGUN-DELAY' in pv_name:
                if not hasattr(self, '_egun_delay'):
                    return UNDEF_VALUE
                return self._egun_delay
            else:
                return None
        else:
            return None

    # --- methods implementing response of model to set requests

    def _set_pv_fake(self, pv_name, value):
        if 'MODE' in pv_name:
            self._single_bunch_mode = value
            return True
        return super()._set_pv_fake(pv_name, value)


    def _set_pv_timing(self, pv_name, value):
        if 'CYCLE' in pv_name:
            self._cycle = value
            self._send_queue.put(('s', (pv_name, 0)))
            self._injection_cycle()
            self._cycle = 0
            return True
        elif 'TI-EGUN-ENABLED' in pv_name:
            self._egun_enabled = value
            return True
        elif 'TI-EGUN-DELAY' in pv_name:
            self._egun_delay = value
            return True
        return False

    # --- methods that help updating the model state

    def _update_state(self):
        pass

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._accelerator = self.model_module.create_accelerator()
        self._lattice_length = 21 #[m]
        self._append_marker()
        self._all_pvs = self.model_module.record_names.get_record_names(self._accelerator)
        self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)
        self._set_vacuum_chamber()
        self._set_nominal_delays()
        self._send_injection_parameters()
        self._egun_enabled = 1
        self._cycle = 0

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        if self._beam_charge: self._beam_charge.dump()
        self._orbit = None
        self._twiss = None
        self._injection_efficiency = 1.0
        self._ejection_efficiency  = 1.0

    # --- auxiliary methods

    def _send_injection_parameters(self):
        _dict = {
            'emittance': self._emittance,
            'energy_spread': self._energy_spread,
            'global_coupling': self._global_coupling,
            'init_twiss': self._twiss_at_exit}
        self._send_parameters_to_downstream_accelerator(_dict)

    def _set_nominal_delays(self):
        self._egun_delay = 0

        # Update epics memory
        self._send_queue.put(('s', ('LITI-EGUN-DELAY', self._egun_delay)))

        # Send path length to downstream accelerator
        _dict = {'path_length': self._lattice_length,
                'bunch_separation': self._pulse_duration/self.nr_bunches,
                'nr_bunches': self.nr_bunches,
                'egun_delay': self._egun_delay}
        self._send_parameters_to_downstream_accelerator(_dict)
        self._send_initialisation_sign()

    def _injection_cycle(self):
        if not self._cycle: return

        self._log(message1 = 'cycle', message2 = '--')
        self._log(message1 = 'cycle', message2='Starting injection')
        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')

        if self._egun_enabled:
            if self._single_bunch_mode:
                charge = [self.model_module.single_bunch_charge]
            else:
                charge = [self.model_module.multi_bunch_charge/self.nr_bunches]*self.nr_bunches
        else:
            charge = [0.0]

        self._log(message1 = 'cycle', message2 = 'electron gun providing charge: {0:.5f} nC'.format(sum(charge)*1e9))
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))
        self._send_parameters_to_downstream_accelerator({'charge' : charge, 'linac_charge': charge})
