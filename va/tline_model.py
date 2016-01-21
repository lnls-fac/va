
import pyaccel
from . import accelerator_model
from . import beam_charge
from . import injection
from . import utils

_c = accelerator_model._c
UNDEF_VALUE = accelerator_model.UNDEF_VALUE

class TLineModel(accelerator_model.AcceleratorModel):

    # --- methods implementing response of model to get requests

    def _get_pv_static(self, pv_name):
        value = super()._get_pv_static(pv_name)
        if value is not None:
            return value
        elif '-BPM-' in pv_name:
            charge = self._beam_charge.total_value
            idx = self._get_elements_indices(pv_name)
            if 'FAM:MONIT:X' in pv_name:
                if self._orbit is None: return [UNDEF_VALUE]*len(idx)
                return self._orbit[0,idx]
            elif 'FAM:MONIT:Y' in pv_name:
                if self._orbit is None: return [UNDEF_VALUE]*len(idx)
                return self._orbit[2,idx]
            elif 'MONIT:X' in pv_name:
                if self._orbit is None: return [UNDEF_VALUE]
                return self._orbit[0,idx[0]]
            elif 'MONIT:Y' in pv_name:
                if self._orbit is None: return [UNDEF_VALUE]
                return self._orbit[2,idx[0]]
            else:
                return None
        else:
            return None

    def _get_pv_timing(self, pv_name):
        if self.prefix == 'TB' and 'TI-' in pv_name:
            if 'SEPTUMINJ-ENABLED' in pv_name:
                return self._injection_magnet_enabled
            elif 'SEPTUMINJ-DELAY' in pv_name:
                if not hasattr(self, '_injection_magnet_delay'):
                    return UNDEF_VALUE
                return self._injection_magnet_delay
            else:
                return None
        elif self.prefix == 'TS' and 'TI-' in pv_name:
            if 'SEPTUMTHICK-ENABLED' in pv_name:
                return self._injection_magnet_enabled
            elif 'SEPTUMTHIN-ENABLED' in pv_name:
                return self._injection_magnet_enabled
            elif 'SEPTUMEX-ENABLED' in pv_name:
                return self._extraction_magnet_enabled
            elif 'SEPTUMTHICK-DELAY' in pv_name:
                if not hasattr(self, '_injection_magnet_delay'):
                    return UNDEF_VALUE
                return self._injection_magnet_delay
            elif 'SEPTUMTHIN-DELAY' in pv_name:
                if not hasattr(self, '_injection_magnet_delay'):
                    return UNDEF_VALUE
                return self._injection_magnet_delay
            elif 'SEPTUMEX-DELAY' in pv_name:
                if not hasattr(self, '_extraction_magnet_delay'):
                    return UNDEF_VALUE
                return self._extraction_magnet_delay
            else:
                return None
        else:
            return None

    # --- methods implementing response of model to set requests

    def _set_pv_timing(self, pv_name, value):
        if self.prefix == 'TB' and 'TI-' in pv_name:
            if 'SEPTUMINJ-ENABLED' in pv_name:
                self._injection_magnet_enabled = value
                return True
            elif 'SEPTUMINJ-DELAY' in pv_name:
                self._injection_magnet_delay = value
                return True
            else:
                return False
        if self.prefix == 'TS' and 'TI-' in pv_name:
            if 'SEPTUMTHICK-ENABLED' in pv_name:
                self._injection_magnet_enabled = value
                return True
            elif 'SEPTUMTHIN-ENABLED' in pv_name:
                self._injection_magnet_enabled = value
                return True
            elif 'SEPTUMEX-ENABLED' in pv_name:
                self._extraction_magnet_enabled = value
                return True
            elif 'SEPTUMTHICK-DELAY' in pv_name:
                self._injection_magnet_delay = value
                return True
            elif 'SEPTUMTHIN-DELAY' in pv_name:
                self._injection_magnet_delay = value
                return True
            elif 'SEPTUMEX-DELAY' in pv_name:
                self._extraction_magnet_delay = value
                return True
            else:
                return False
        else:
            return False

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._state_deprecated or self._update_injection_efficiency:
            self._calc_transport_efficiency()
            self._state_deprecated = False
            self._update_injection_efficiency = False
            self._state_changed = True

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._accelerator = self.model_module.create_accelerator()
        self._lattice_length = pyaccel.lattice.length(self._accelerator)
        self._append_marker()
        self._all_pvs = self.model_module.device_names.get_device_names(self._accelerator)
        self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)
        self._set_vacuum_chamber()
        self._injection_magnet_enabled  = 1
        self._extraction_magnet_enabled = 1
        self._state_deprecated = True
        self._update_state()

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        if self._beam_charge: self._beam_charge.dump()
        self._orbit = None
        self._twiss = None
        self._injection_parameters = None
        self._transport_efficiency = None

    # --- auxiliary methods

    def _calc_nominal_delays(self, path_length=None, bunch_separation=None, nr_bunches=None, egun_delay=None):
        self._bunch_separation = bunch_separation
        half_pulse_duration = nr_bunches*self._bunch_separation/2.0

        # Calculate extraction septum nominal delay
        if self._has_extraction_pulsed_magnet:
            self._extraction_magnet_nominal_delay = egun_delay + path_length/_c - self._extraction_magnet_rise_time + half_pulse_duration
            self._extraction_magnet_delay = self._extraction_magnet_nominal_delay

        # Calculate injection septum nominal delay
        if self._has_injection_pulsed_magnet:
            self._injection_magnet_idx = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', self._injection_magnet_label)[0]
            length = path_length + pyaccel.lattice.length(self._accelerator[:self._injection_magnet_idx])
            self._injection_magnet_nominal_delay = egun_delay + length/_c - self._injection_magnet_rise_time + half_pulse_duration
            self._injection_magnet_delay = self._injection_magnet_nominal_delay

        # Update epics memory
        self._update_delay_pvs_in_epics_memory()

        # Send path length to downstream accelerator
        _dict = {'path_length': path_length + self._lattice_length,
                'bunch_separation': bunch_separation,
                'nr_bunches': nr_bunches,
                'egun_delay': egun_delay}
        self._send_parameters_to_downstream_accelerator(_dict)
        self._send_initialisation_sign()

    def _update_delay_pvs_in_epics_memory(self):
        if self.prefix == 'TB':
            self._send_queue.put(('s', ('TBTI-SEPTUMINJ-DELAY', self._injection_magnet_nominal_delay)))
        else:
            self._send_queue.put(('s', ('TSTI-SEPTUMEX-DELAY', self._extraction_magnet_nominal_delay)))
            self._send_queue.put(('s', ('TSTI-SEPTUMTHICK-DELAY', self._injection_magnet_nominal_delay)))
            self._send_queue.put(('s', ('TSTI-SEPTUMTHIN-DELAY',  self._injection_magnet_nominal_delay)))

    def _calc_transport_efficiency(self):
        if self._injection_parameters is None: return
        self._log('calc', 'transport efficiency  for '+self.model_module.lattice_version)
        _dict = {}
        _dict.update(self._injection_parameters)
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())

        loss_fraction, self._twiss, self._m66 = \
            injection.calc_charge_loss_fraction_in_line(self._accelerator, **_dict)
        self._transport_efficiency = 1.0 - loss_fraction
        self._orbit = self._twiss.co

        args_dict = {}
        args_dict.update(self._injection_parameters)
        args_dict['init_twiss'] = self._twiss[-1].make_dict() # picklable object
        self._send_parameters_to_downstream_accelerator(args_dict)

    def _calc_extraction_magnet_efficiency(self, nr_bunches):
        rise_time     = self._extraction_magnet_rise_time
        delay         = self._extraction_magnet_delay
        nominal_delay = self._extraction_magnet_nominal_delay
        efficiency = injection.calc_pulsed_magnet_efficiency(rise_time, delay, nominal_delay, self._bunch_separation, nr_bunches)
        return efficiency

    def _calc_injection_magnet_efficiency(self, nr_bunches):
        rise_time     = self._injection_magnet_rise_time
        delay         = self._injection_magnet_delay
        nominal_delay = self._injection_magnet_nominal_delay
        efficiency = injection.calc_pulsed_magnet_efficiency(rise_time, delay, nominal_delay, self._bunch_separation, nr_bunches)
        return efficiency

    def _injection_cycle(self, **kwargs):
        charge = kwargs['charge']

        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        nr_bunches = len(charge)
        initial_charge = charge

        if self._has_extraction_pulsed_magnet:
            extraction_magnet_efficiency = self._calc_extraction_magnet_efficiency(nr_bunches)
            charge = charge*extraction_magnet_efficiency

        charge = [bunch_charge * self._transport_efficiency for bunch_charge in charge]

        if self._has_injection_pulsed_magnet:
            injection_magnet_efficiency = self._calc_injection_magnet_efficiency(nr_bunches)
            charge = charge*injection_magnet_efficiency

        self._log(message1='cycle', message2='beam transport at {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*(sum(charge)/sum(initial_charge))))

        kwargs['charge'] = charge
        self._send_parameters_to_downstream_accelerator(kwargs)
