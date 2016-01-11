
import pyaccel
from . import accelerator_model
from . import beam_charge
from . import injection
from . import utils


class TLineModel(accelerator_model.AcceleratorModel):

    # --- methods implementing response of model to get requests

    def _get_pv_fake(self, pv_name):
        return super()._get_pv_fake(pv_name)

    def _get_pv_timing(self, pv_name):
        if self.prefix == 'TB' and 'TI-' in pv_name:
            if 'SEPTUMINJ-ENABLED' in pv_name:
                return self._ti_septuminj_enabled
            elif 'SEPTUMINJ-DELAY' in pv_name:
                return self._ti_septuminj_delay
            else:
                return None
        elif self.prefix == 'TS' and 'TI-' in pv_name:
            if 'SEPTUMTHICK-ENABLED' in pv_name:
                return self._ti_septumthick_enabled
            elif 'SEPTUMTHICK-DELAY' in pv_name:
                return self._ti_septumthick_delay
            elif 'SEPTUMTHIN-ENABLED' in pv_name:
                return self._ti_septumthin_enabled
            elif 'SEPTUMTHIN-DELAY' in pv_name:
                return self._ti_septumthin_delay
            elif 'SEPTUMEX-ENABLED' in pv_name:
                return self._ti_septumex_enabled
            elif 'SEPTUMEX-DELAY' in pv_name:
                return self._ti_septumex_delay
            else:
                return None
        else:
            return None

    # --- methods implementing response of model to set requests

    def _set_pv_fake(self, pv_name, value):
        return super()._set_pv_fake(pv_name, value)

    def _set_pv_timing(self, pv_name, value):
        if self.prefix == 'TB' and 'TI-' in pv_name:
            if 'SEPTUMINJ-ENABLED' in pv_name:
                self._ti_septuminj_enabled = value
                self._state_deprecated = True
                return True
            elif 'SEPTUMINJ-DELAY' in pv_name:
                self._ti_septuminj_delay = value
                self._state_deprecated = True
                return True
            else:
                return False
        if self.prefix == 'TS' and 'TI-' in pv_name:
            if 'SEPTUMTHICK-ENABLED' in pv_name:
                self._ti_septumthick_enabled = value
                self._state_deprecated = True
                return True
            elif 'SEPTUMTHICK-DELAY' in pv_name:
                self._ti_septumthick_delay = value
                self._state_deprecated = True
                return True
            elif 'SEPTUMTHIN-ENABLED' in pv_name:
                self._ti_septumthin_enabled = value
                self._state_deprecated = True
                return True
            elif 'SEPTUMTHIN-DELAY' in pv_name:
                self._ti_septumthin_delay = value
                self._state_deprecated = True
                return True
            elif 'SEPTUMEX-ENABLED' in pv_name:
                self._ti_septumex_enabled = value
                self._state_deprecated = True
                return True
            elif 'SEPTUMEX-DELAY' in pv_name:
                self._ti_septumex_delay = value
                self._state_deprecated = True
                return True
            else:
                return False
        else:
            return False

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._state_deprecated or self._update_injection_efficiency:
            self._calc_injection_efficiency()
            self._state_deprecated = False
            self._update_injection_efficiency = False
            self._state_changed = True

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._accelerator = self.model_module.create_accelerator()
        self._append_marker()
        self._all_pvs = self.model_module.record_names.get_record_names(self._accelerator)
        self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)
        self._set_vacuum_chamber()

        # initial values of timing pvs
        if self.prefix == 'TB':
            self._ti_septuminj_enabled = 1
            self._ti_septuminj_delay = 0
        if self.prefix == 'TS':
            self._ti_septumthick_enabled = 1
            self._ti_septumthick_delay = 0
            self._ti_septumthin_enabled = 1
            self._ti_septumthin_delay = 0
            self._ti_septumex_enabled = 1
            self._ti_septumex_delay = 0
            
        self._state_deprecated = True
        self._update_state()

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        if self._beam_charge: self._beam_charge.dump()
        self._orbit = None
        self._twiss = None
        self._injection_parameters = None
        self._injection_efficiency = None
        self._ejection_efficiency  = 1.0

    # --- auxiliary methods

    def _calc_injection_efficiency(self):
        if self._injection_parameters is None: return
        self._log('calc', 'transport efficiency  for '+self.model_module.lattice_version)
        _dict = {}
        _dict.update(self._injection_parameters)
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())

        loss_fraction, self._twiss, self._m66 = \
            injection.calc_charge_loss_fraction_in_line(self._accelerator, **_dict)
        self._injection_efficiency = 1.0 - loss_fraction
        self._orbit = self._twiss.co

        args_dict = {}
        args_dict.update(self._injection_parameters)
        args_dict['init_twiss'] = self._twiss[-1].make_dict() # picklable object
        self._send_parameters_to_downstream_accelerator(args_dict)

    def _injection(self, charge=None, delay=0.0, li_charge=None):
        if charge is None: return
        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        self._beam_inject(charge=charge)
        self._log(message1='cycle', message2='beam injection at {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*self._injection_efficiency))

        final_charge = self._beam_eject()
        self._send_charge_to_downstream_accelerator({'charge' : final_charge, 'delay' : delay, 'li_charge': li_charge})
