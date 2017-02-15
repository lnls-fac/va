
import pyaccel
from . import accelerator_model
from . import beam_charge
from . import utils


UNDEF_VALUE = accelerator_model.UNDEF_VALUE


class LinacModel(accelerator_model.AcceleratorModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._set_pulsed_magnets_parameters()

    # --- methods implementing response of model to get requests

    def _get_pv_fake(self, pv_name):
        if 'Mode' in pv_name:
            return self._single_bunch_mode
        return super()._get_pv_fake(pv_name)


    def _get_pv_timing(self, pv_name):
        value = super()._get_pv_timing(pv_name)
        if value is not None: return value
        _dict = self.model_module.device_names.split_name(pv_name)
        discipline = _dict['discipline']
        device = _dict['device']
        proper = _dict['property']

        if not discipline == 'TI': return None

        if device == 'Cycle':
            if proper == 'StartInj':
                return self._cycle
            elif proper == 'InjBun':
                if not hasattr(self, '_injection_bunch'):
                    return UNDEF_VALUE
                return self._injection_bunch
        if device == 'EGun':
            if proper == 'Enbl': return self._egun_enabled
            elif proper =='Delay':
                if not hasattr(self, '_egun_delay'):
                    return UNDEF_VALUE
                return self._egun_delay
        else:
            return None


    # --- methods implementing response of model to set requests

    def _set_pv_fake(self, pv_name, value):
        if 'Mode' in pv_name:
            self._single_bunch_mode = value
            return True
        return super()._set_pv_fake(pv_name, value)


    def _set_pv_timing(self, pv_name, value):
        if super()._set_pv_timing(pv_name, value): return
        _dict = self.model_module.device_names.split_name(pv_name)
        discipline = _dict['discipline']
        device = _dict['device']
        proper = _dict['property']

        if not discipline == 'TI': return False
        if device == 'Cycle':
            if proper == 'StartInj':
                self._cycle = value
                self._send_queue.put(('s', (pv_name, 0)))
                self._injection_cycle()
                self._cycle = 0
                return True
            elif proper == 'InjBun':
                injection_bunch = int(value)
                self._master_delay = injection_bunch*self._bunch_separation
                return True
        elif device == 'EGun':
            if proper == 'Enbl': self._egun_enabled = value
            elif proper == 'Delay': self._egun_delay = value
            else: return False
            return True
        return False

    # --- methods that help updating the model state

    def _update_state(self):
        pass

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._accelerator,_ = self.model_module.create_accelerator()
        self._append_marker()
        self._all_pvs = self.model_module.device_names.get_device_names(self._accelerator)
        #self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)
        self._set_vacuum_chamber()
        self._send_injection_parameters()
        self._bunch_separation = 6*(1/self._frequency)
        self._egun_enabled = 1
        self._egun_delay = 0
        self._master_delay = 0
        self._single_bunch_mode = 0
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
        _dict = { 'injection_parameters' : {
            'emittance': self._emittance,
            'energy_spread': self._energy_spread,
            'global_coupling': self._global_coupling,
            'init_twiss': self._twiss_at_exit}
        }
        self._send_parameters_to_downstream_accelerator(_dict)

    def _set_pulsed_magnets_parameters(self):
        _dict = { 'pulsed_magnet_parameters' : {
            'total_length'      : self._accelerator.length,
            'magnet_pos'        : 0,
            'nominal_delays'    : {'EGun' : self._egun_delay},}
        }
        self._send_parameters_to_downstream_accelerator(_dict)

    def _update_pulsed_magnets_delays(self, delays):
        for magnet_name, delay in delays.items():
            if 'EGun' in magnet_name:
                self._egun_delay = delay
        self._update_delay_pvs_in_epics_memory()
        self._send_parameters_to_downstream_accelerator({'update_delays' : delays})
        self._send_initialisation_sign()

    def _update_delay_pvs_in_epics_memory(self):
        pv_name = self.model_module.device_names.join_name('TI','EGun','01',proper='Delay')
        self._send_queue.put(('s', (pv_name, self._egun_delay)))

    def _injection_cycle(self):
        if not self._cycle: return

        self._log(message1 = 'cycle', message2 = '--')
        self._log(message1 = 'cycle', message2='Starting injection')
        self._log(message1 = 'cycle', message2 = '-- ' + self.prefix + ' --')

        if self._egun_enabled:
            if self._single_bunch_mode:
                charge = [self._single_bunch_charge]
            else:
                charge = [self._multi_bunch_charge/self.nr_bunches]*self.nr_bunches
        else:
            self._log(message1 = 'cycle', message2 = 'electron gun providing charge: {0:.5f} nC'.format(0.0))
            self._log(message1 = 'cycle', message2 = 'Stoping injection')
            return

        self._log(message1 = 'cycle', message2 = 'electron gun providing charge: {0:.5f} nC'.format(sum(charge)*1e9))
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        charge_time = [self._master_delay + self._egun_delay + i*self._bunch_separation for i in range(len(charge))]

        _dict = {'injection_cycle' : {'charge': charge,
                                      'charge_time': charge_time,
                                      'master_delay': self._master_delay,
                                      'bunch_separation': self._bunch_separation}}
        self._send_parameters_to_downstream_accelerator(_dict)
