
import pyaccel
from . import accelerator_model
from . import beam_charge
from . import injection
from . import utils

calc_injection_eff = accelerator_model.calc_injection_eff
UNDEF_VALUE = accelerator_model.UNDEF_VALUE


class LinacModel(accelerator_model.AcceleratorModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._set_pulsed_magnets_parameters()
        self._injection_bunch = 1

    # --- methods implementing response of model to get requests

    def _get_pv_fake(self, pv_name, name_parts):
        Discipline = name_parts['Discipline']
        if Discipline == 'FK' and 'Mode' in pv_name:
            return self._single_bunch_mode
        return super()._get_pv_fake(pv_name, name_parts)


    def _get_pv_timing(self, pv_name, name_parts):
        value = super()._get_pv_timing(pv_name, name_parts)
        if value is not None: return value

        Discipline = name_parts['Discipline']
        Device     = name_parts['Device']
        Property   = name_parts['Property']
        if not Discipline == 'TI': return None
        if Device == 'Cycle':
            elif Property == 'InjBun':
                if not hasattr(self, '_injection_bunch'):
                    return UNDEF_VALUE
                return self._injection_bunch
        if Device == 'EGun':
            if Property == 'Enbl': return self._egun_enabled
            elif Property =='Delay':
                if not hasattr(self, '_egun_delay'):
                    return UNDEF_VALUE
                return self._egun_delay
        else:
            return None


    # --- methods implementing response of model to set requests

    def _set_pv_fake(self, pv_name, value, name_parts):
        Discipline = name_parts['Discipline']
        Device     = name_parts['Device']
        Property   = name_parts['Property']
        if Discipline == 'FK' and 'Mode' in pv_name:
            self._single_bunch_mode = value
            return True
        return super()._set_pv_fake(pv_name, value, name_parts)


    def _set_pv_timing(self, pv_name, value, name_parts):
        if super()._set_pv_timing(pv_name, value, name_parts): return

        Discipline = name_parts['Discipline']
        Device     = name_parts['Device']
        Property   = name_parts['Property']
        if not Discipline == 'TI': return False
        if Device == 'Cycle':
            if Property == 'StartInj-Cmd':
                self._send_queue.put(('s', (pv_name, 0)))
                self._injection_cycle()
                return True
            elif Property == 'InjBun':
                self._injection_bunch = int(value)
                self._master_delay = self._injection_bunch*self._bunch_separation
                return True
        elif Device == 'EGun':
            if Property == 'Enbl': self._egun_enabled = value
            elif Property == 'Delay': self._egun_delay = value
            else: return False
            return True
        return False

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._state_deprecated or self._update_injection_efficiency:
            self._calc_transport_efficiency()
            self._state_deprecated = False
            self._update_injection_efficiency = False
            self._state_changed = True

    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._accelerator,_ = self.model_module.create_accelerator()
        self._lattice_length = pyaccel.lattice.length(self._accelerator)
        self._append_marker()
        self._all_pvs = self.model_module.device_names.get_device_names(self._accelerator)
        #self._all_pvs.update(self.pv_module.get_fake_record_names(self._accelerator))
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)
        self._set_vacuum_chamber()
        self._state_deprecated = True
        self._update_state()
        self._bunch_separation = 6*(1/self._frequency)
        self._egun_enabled = 1
        self._egun_delay = 0
        self._master_delay = 0
        self._single_bunch_mode = 0

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        if self._beam_charge: self._beam_charge.dump()
        self._orbit = None
        self._twiss = None
        self._injection_efficiency = 1.0
        self._ejection_efficiency  = 1.0

    # --- auxiliary methods

    def _calc_transport_efficiency(self):
        inj_params =  {
            'emittance': self._emittance,
            'energy_spread': self._energy_spread,
            'global_coupling': self._global_coupling,
            'init_twiss': self._twiss_at_match}

        self._log('calc', 'transport efficiency  for ' + self.model_module.lattice_version)
        _dict = {}
        _dict.update(inj_params)
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())

        idx = pyaccel.lattice.find_indices(self._accelerator,'fam_name','twiss_at_match')
        acc = self._accelerator[idx:]
        loss_fraction, self._twiss, self._m66 = injection.calc_charge_loss_fraction_in_line(acc, **_dict)
        self._transport_efficiency = 1.0 - loss_fraction
        self._orbit = self._twiss.co

        args_dict = {}
        args_dict.update(inj_params)
        args_dict['init_twiss'] = self._twiss[-1].make_dict() # picklable object
        self._send_parameters_to_downstream_accelerator({'injection_parameters' : args_dict})

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

        if calc_injection_eff:
            efficiency = self._transport_efficiency if self._transport_efficiency is not None else 0
            charge = [bunch_charge * efficiency for bunch_charge in charge]
            self._log(message1='cycle', message2='beam transport at {0:s}: {1:.4f}% efficiency'.format(self.prefix, 100*efficiency))

        _dict = {'injection_cycle' : {'charge': charge,
                                      'charge_time': charge_time,
                                      'master_delay': self._master_delay,
                                      'bunch_separation': self._bunch_separation}}
        self._send_parameters_to_downstream_accelerator(_dict)
