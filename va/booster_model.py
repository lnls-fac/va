
import pyaccel
from . import ring_model
from . import utils

class BoosterModel(ring_model.RingModel):

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._upstream_accelerator_state_deprecated:
            self._upstream_accelerator_state_deprecated = False
            # injection
            self._set_kickin('on')
            self._calc_injection_loss_fraction()
            self._set_kickin('off')

        if force or self._state_deprecated:
            self._state_deprecated = False
            self._calc_closed_orbit()
            self._calc_linear_optics()
            self._calc_equilibrium_parameters()
            self._calc_lifetimes()
            # injection
            self._set_kickin('on')
            self._calc_injection_loss_fraction()
            self._set_kickin('off')
            # acceleration
            self._calc_acceleration_loss_fraction()
            # ejection
            self._set_kickex('on')
            self._calc_ejection_loss_fraction()
            self._set_kickex('off')


    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._beam_charge  = utils.BeamCharge(nr_bunches = self._nr_bunches)
        self._beam_dump(message1,message2,c,a)
        accelerator        = self.model_module.create_accelerator()
        injection_point    = pyaccel.lattice.find_indices(accelerator, 'fam_name', 'sept_in')[0]
        self._accelerator  = pyaccel.lattice.shift(accelerator, start = injection_point)
        self._all_pvs      = utils.shift_record_names(self._accelerator, self._all_pvs)
        self._ext_point    = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'sept_ex')[0]
        self._kickin_idx   = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'kick_in')
        self._kickex_idx   = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'kick_ex')
        self._set_vacuum_chamber(indices='open')
        self._update_state()

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        super()._beam_dump(message1=message1, message2=message2, c=c, a=a)
        self._injection_parameters = None
        self._acceleration_loss_fraction = None

    def _beam_accelerate(self):
        efficiency = 1.0 - self._acceleration_loss_fraction
        final_charge = self._beam_charge.value
        self._log(message1='cycle', message2='beam acceleration at {0:s}: {1:.2f}% efficiency'.format(self.model_module.lattice_version, 100*efficiency))

    # --- auxilliary methods

    def _get_equilibrium_at_maximum_energy(self):
        eq = dict()
        eq['emittance']       = self._summary['natural_emittance']
        eq['energy_spread']   = self._summary['natural_energy_spread']
        eq['global_coupling'] = self.model_module.accelerator_data['global_coupling']
        return eq

    def _set_kickin(self, str ='off'):
        for idx in self._kickin_idx:
            if str.lower() == 'on':
                self._accelerator[idx].hkick_polynom = self._kickin_angle
            elif str.lower() == 'off':
                self._accelerator[idx].hkick_polynom = 0.0

    def _set_kickex(self, str ='off'):
        for idx in self._kickex_idx:
            if str.lower() == 'on':
                self._accelerator[idx].hkick_polynom = self._kickex_angle
            elif str.lower() == 'off':
                self._accelerator[idx].hkick_polynom = 0.0

    def _calc_injection_loss_fraction(self):
        if self._injection_parameters is None: return
        self._log('calc', 'injection efficiency  for '+self.model_module.lattice_version)

        args_dict = self._injection_parameters
        args_dict.update(self._get_vacuum_chamber())
        args_dict.update(self._get_coordinate_system_parameters())
        self._injection_loss_fraction = utils.charge_loss_fraction_ring(self._accelerator, **args_dict)

    def _calc_acceleration_loss_fraction(self):
        self._log('calc', 'acceleration efficiency  for '+self.model_module.lattice_version)
        self._acceleration_loss_fraction = 0.0

    def _calc_ejection_loss_fraction(self):
        if self._twiss is None: return
        self._log('calc', 'ejection efficiency  for '+self.model_module.lattice_version)

        accelerator = self._accelerator[self._kickex_idx[0]:self._ext_point+1]
        ejection_parameters = self._get_equilibrium_at_maximum_energy()
        args_dict = ejection_parameters
        args_dict.update(self._get_vacuum_chamber(init_idx=self._kickex_idx[0], final_idx=self._ext_point+1))
        self._ejection_loss_fraction, twiss, *_ = utils.charge_loss_fraction_line(accelerator,
            init_twiss=self._twiss[self._kickex_idx[0]], **args_dict)
        self._send_parameters_to_downstream_accelerator(twiss[-1], ejection_parameters)

    def _receive_synchronism_signal(self):
        self._log(message1 = 'cycle', message2 = self.prefix, c='white')
        charge=self._charge_to_inject
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.model_module.lattice_version, sum(charge)*1e9), c='white')
        self._beam_inject(charge=charge, message1='cycle')
        self._charge_to_inject = 0.0
        self._beam_accelerate()
        final_charge = self._beam_eject(message1='cycle')
        self._send_charge_to_downstream_accelerator(final_charge)
