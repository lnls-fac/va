
import pyaccel
from . import accelerator_model
from . import beam_charge
from . import injection
from . import utils

_c = accelerator_model._c
UNDEF_VALUE = accelerator_model.UNDEF_VALUE

class TLineModel(accelerator_model.AcceleratorModel):

    # --- methods implementing response of model to get requests

    def _get_pv_timing(self, pv_name):
        if self.prefix == 'TB' and 'TI-' in pv_name:
            if 'SEPTUMINJ-ENABLED' in pv_name:
                return self._septuminj_enabled
            elif 'SEPTUMINJ-DELAY' in pv_name:
                if not hasattr(self, '_septuminj_delay'):
                    return UNDEF_VALUE
                return self._septuminj_delay
            else:
                return None
        elif self.prefix == 'TS' and 'TI-' in pv_name:
            if 'SEPTUMTHICK-ENABLED' in pv_name:
                return self._septumthick_enabled
            elif 'SEPTUMTHIN-ENABLED' in pv_name:
                return self._septumthin_enabled
            elif 'SEPTUMEX-ENABLED' in pv_name:
                return self._septumex_enabled
            elif 'SEPTUMTHICK-DELAY' in pv_name:
                if not hasattr(self, '_septumthick_delay'):
                    return UNDEF_VALUE
                return self._septumthick_delay
            elif 'SEPTUMTHIN-DELAY' in pv_name:
                if not hasattr(self, '_septumthin_delay'):
                    return UNDEF_VALUE
                return self._septumthin_delay
            elif 'SEPTUMEX-DELAY' in pv_name:
                if not hasattr(self, '_septumex_delay'):
                    return UNDEF_VALUE
                return self._septumex_delay
            else:
                return None
        else:
            return None

    # --- methods implementing response of model to set requests

    def _set_pv_timing(self, pv_name, value):
        if self.prefix == 'TB' and 'TI-' in pv_name:
            if 'SEPTUMINJ-ENABLED' in pv_name:
                self._septuminj_enabled = value
                return True
            elif 'SEPTUMINJ-DELAY' in pv_name:
                self._septuminj_delay = value
                return True
            else:
                return False
        if self.prefix == 'TS' and 'TI-' in pv_name:
            if 'SEPTUMTHICK-ENABLED' in pv_name:
                self._septumthick_enabled = value
                return True
            elif 'SEPTUMTHIN-ENABLED' in pv_name:
                self._septumthin_enabled = value
                return True
            elif 'SEPTUMEX-ENABLED' in pv_name:
                self._septumex_enabled = value
                return True
            elif 'SEPTUMTHICK-DELAY' in pv_name:
                self._septumthick_delay = value
                return True
            elif 'SEPTUMTHIN-DELAY' in pv_name:
                self._septumthin_delay = value
                return True
            elif 'SEPTUMEX-DELAY' in pv_name:
                self._septumex_delay = value
                return True
            else:
                return False
        else:
            return False

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._state_deprecated or self._update_injection_efficiency:
            #self._calc_injection_efficiency()
            self._state_deprecated = False
            self._update_injection_efficiency = False
            self._state_changed = True

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._accelerator = self.model_module.create_accelerator()
        self._lattice_length = pyaccel.lattice.length(self._accelerator)
        self._append_marker()
        self._septuminj_idx = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', self._injection_septum_label)[0]
        self._all_pvs = self.model_module.record_names.get_record_names(self._accelerator)
        self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)
        self._set_vacuum_chamber()
        self._septuminj_enabled = 1
        self._septumex_enabled = 1
        self._septumthick_enabled = 1
        self._septumthin_enabled = 1
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

    def _calc_nominal_delays(self, **kwargs):
        if self.prefix == 'TB':
            self._calc_tb_nominal_delays(**kwargs)
        elif self.prefix == 'TS':
            self._calc_ts_nominal_delays(**kwargs)
        self._send_initialisation_sign()

    def _calc_tb_nominal_delays(self, path_length=None, pulse_duration=None):
        # Calculate injection septum nominal delay
        length = path_length + pyaccel.lattice.length(self._accelerator[:self._septuminj_idx])
        self._septuminj_nominal_delay = length/_c - self._injection_septum_rise_time + pulse_duration/2.0
        self._septuminj_delay = self._septuminj_nominal_delay

        # Update epics memory
        self._send_queue.put(('s', ('TBTI-SEPTUMINJ-DELAY', self._septuminj_nominal_delay)))

        # Send path length to downstream accelerator
        _dict = {'path_length': path_length + self._lattice_length, 'pulse_duration': pulse_duration}
        self._send_parameters_to_downstream_accelerator(_dict)

    def _calc_ts_nominal_delays(self, path_length=None, pulse_duration=None):
        # Calculate extraction septum nominal delay
        self._septumex_nominal_delay = path_length/_c - self._extraction_septum_rise_time + pulse_duration/2.0
        self._septumex_delay = self._septumex_nominal_delay

        # Calculate injection septum nominal delay
        length = path_length + pyaccel.lattice.length(self._accelerator[:self._septuminj_idx])
        self._septuminj_nominal_delay = length/_c - self._injection_septum_rise_time + pulse_duration/2.0
        self._septumthick_delay = self._septuminj_nominal_delay
        self._septumthin_delay = self._septuminj_nominal_delay

        # Update epics memory
        self._send_queue.put(('s', ('TSTI-SEPTUMEX-DELAY', self._septumex_nominal_delay)))
        self._send_queue.put(('s', ('TSTI-SEPTUMTHICK-DELAY', self._septuminj_nominal_delay)))
        self._send_queue.put(('s', ('TSTI-SEPTUMTHIN-DELAY',  self._septuminj_nominal_delay)))

        # Send path length to downstream accelerator
        _dict = {'path_length': path_length + self._lattice_length, 'pulse_duration': pulse_duration}
        self._send_parameters_to_downstream_accelerator(_dict)

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

    def _injection(self, charge=None, li_charge=None):
        if charge is None: return
        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        self._beam_inject(charge=charge)
        self._log(message1='cycle', message2='beam injection at {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*self._injection_efficiency))

        final_charge = self._beam_eject()
        self._send_charge_to_downstream_accelerator({'charge' : final_charge, 'li_charge': li_charge})
