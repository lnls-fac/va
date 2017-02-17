
import pyaccel
from . import accelerator_model
from . import beam_charge
from . import injection


calc_injection_eff = accelerator_model.calc_injection_eff
calc_timing_eff = accelerator_model.calc_timing_eff
UNDEF_VALUE = accelerator_model.UNDEF_VALUE
orbit_unit = accelerator_model.orbit_unit


class TLineModel(accelerator_model.AcceleratorModel):

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

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        if self._beam_charge: self._beam_charge.dump()
        self._orbit = None
        self._twiss = None
        self._injection_parameters = None
        self._transport_efficiency = None

    # --- auxiliary methods

    def _set_pulsed_magnets_parameters(self, **kwargs):
        if 'total_length' in kwargs:
            prev_total_length = kwargs['total_length']
        if 'magnet_pos' in kwargs:
            prev_magnet_pos = kwargs['magnet_pos']
        if 'nominal_delays' in kwargs:
            nominal_delays = kwargs['nominal_delays']

        for ps in self._pulsed_power_supplies.values(): ps.turn_off()

        magnets_pos = dict()
        for magnet_name, magnet in self._pulsed_magnets.items():
            magnet_pos = prev_total_length + magnet.length_to_inj_point
            magnet.length_to_egun = magnet_pos
            magnets_pos[magnet_name] = magnet_pos
        sorted_magnets_pos = sorted(magnets_pos.items(), key=lambda x: x[1])

        for i in range(len(sorted_magnets_pos)):
            magnet_name, magnet_pos = sorted_magnets_pos[i]
            magnet = self._pulsed_magnets[magnet_name]
            magnet.length_to_prev_pulsed_magnet = magnet_pos - prev_magnet_pos
            nominal_delays[magnet_name] = magnet.delay
            prev_magnet_pos = magnet_pos

        total_length = prev_total_length + self._accelerator.length

        _dict = { 'pulsed_magnet_parameters' : {
            'total_length'     : total_length,
            'magnet_pos'       : magnet_pos,
            'nominal_delays'   : nominal_delays,}
        }
        self._send_parameters_to_downstream_accelerator(_dict)

    def _update_pulsed_magnets_delays(self, delays):
        for magnet_name, delay in delays.items():
            if magnet_name in self._pulsed_magnets.keys():
                self._pulsed_magnets[magnet_name].delay = delay
        self._update_delay_pvs_in_epics_memory()
        self._send_parameters_to_downstream_accelerator({'update_delays' : delays})
        self._send_initialisation_sign()

    def _update_delay_pvs_in_epics_memory(self):
        for magnet_name, magnet in self._pulsed_magnets.items():
            pv_name = self._magnet2delay[magnet_name]
            value = magnet.delay
            self._send_queue.put(('s', (pv_name, value)))

    def _calc_transport_efficiency(self):
        if self._injection_parameters is None: return
        self._log('calc', 'transport efficiency  for ' + self.model_module.lattice_version)
        _dict = {}
        _dict.update(self._injection_parameters)
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())

        for ps in self._pulsed_power_supplies.values(): ps.turn_on()
        loss_fraction, self._twiss, self._m66 = injection.calc_charge_loss_fraction_in_line(self._accelerator, **_dict)
        self._transport_efficiency = 1.0 - loss_fraction
        self._orbit = self._twiss.co
        for ps in self._pulsed_power_supplies.values(): ps.turn_off()

        args_dict = {}
        args_dict.update(self._injection_parameters)
        args_dict['init_twiss'] = self._twiss[-1].make_dict() # picklable object
        self._send_parameters_to_downstream_accelerator({'injection_parameters' : args_dict})

    def _injection_cycle(self, **kwargs):
        charge = kwargs['charge']
        charge_time = kwargs['charge_time']

        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        if calc_timing_eff:
            prev_charge = sum(charge)
            for magnet in self._get_sorted_pulsed_magnets():
                charge, charge_time = magnet.pulsed_magnet_pass(charge, charge_time, kwargs['master_delay'])
            efficiency = (sum(charge)/prev_charge) if prev_charge != 0 else 0
            self._log(message1='cycle', message2='pulsed magnets in {0:s}: {1:.4f}% efficiency'.format(self.prefix, 100*efficiency))

        if calc_injection_eff:
            efficiency = self._transport_efficiency if self._transport_efficiency is not None else 0
            if 'ejection_efficiency' in kwargs: efficiency = efficiency*kwargs['ejection_efficiency']
            charge = [bunch_charge * efficiency for bunch_charge in charge]
            self._log(message1='cycle', message2='beam transport at {0:s}: {1:.4f}% efficiency'.format(self.prefix, 100*efficiency))

        kwargs['charge'] = charge
        kwargs['charge_time'] = charge_time
        self._send_parameters_to_downstream_accelerator({'injection_cycle' : kwargs})
        print(self.prefix)
