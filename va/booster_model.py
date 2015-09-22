
import pyaccel
from . import ring_model
from . import beam_charge
from . import injection
from . import utils

TRACK6D = ring_model.TRACK6D 

class BoosterModel(ring_model.RingModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Send value of BOTI-KICKEX-INC to SI
        self._send_queue.put(('g', ('SI', 'BOTI-KICKEX-INC')))

    # --- methods implementing response of model to get requests

    def _get_pv_timing(self, pv_name):
        if 'TI-' in pv_name:
            if 'KICKINJ-ENABLED' in pv_name:
                return self._ti_kickinj_enabled
            elif 'KICKINJ-DELAY' in pv_name:
                return self._ti_kickinj_delay
            elif 'KICKEX-ENABLED' in pv_name:
                return self._ti_kickex_enabled
            elif 'KICKEX-DELAY' in pv_name:
                return self._ti_kickex_delay
            elif 'KICKEX-INC' in pv_name:
                return self._ti_kickex_inc
            elif 'RAMPPS-ENABLED' in pv_name:
                return self._ti_rampps_enabled
            elif 'RAMPPS-DELAY' in pv_name:
                return self._ti_rampps_delay
            else:
                return None
        else:
            return None

    # --- methods implementing response of model to set requests

    def _set_pv_timing(self, pv_name, value):
        if 'TI-' in pv_name:
            if 'KICKINJ-ENABLED' in pv_name:
                self._ti_kickinj_enabled = value
                self._state_deprecated = True
                return True
            elif 'KICKINJ-DELAY' in pv_name:
                self._ti_kickinj_delay = value
                self._state_deprecated = True
                return True
            elif 'KICKEX-ENABLED' in pv_name:
                self._ti_kickex_enabled = value
                self._state_deprecated = True
                return True
            elif 'KICKEX-DELAY' in pv_name:
                self._ti_kickex_delay = value
                self._state_deprecated = True
                return True
            elif 'KICKEX-INC' in pv_name:
                self._ti_kickex_inc = value
                self._send_queue.put(('g', ('SI', 'BOTI-KICKEX-INC')))
                self._state_deprecated = True
                return True
            elif 'RAMPPS-ENABLED' in pv_name:
                self._ti_rampps_enabled = value
                self._state_deprecated = True
                return True
            elif 'RAMPPS-DELAY' in pv_name:
                self._ti_rampps_delay = value
                self._state_deprecated = True
                return True
            else:
                return False
        else:
            return False

    # --- methods that help updating the model state

    def _update_state(self, force=False):

        if force or self._state_deprecated:
            self._calc_closed_orbit()
            self._calc_linear_optics()
            self._calc_equilibrium_parameters()
            self._calc_lifetimes()
            self._calc_injection_efficiency = True
            self._calc_acceleration_efficiency = True
            self._calc_ejection_efficiency = True
            self._state_changed = True
            self._state_deprecated = False

        # Calculate injection efficiency
        if self._calc_injection_efficiency and (self._received_charge or self._injection_loss_fraction is None):
            self._calc_injection_efficiency = False
            self._set_kickin('on')
            self._calc_injection_loss_fraction()
            self._set_kickin('off')

        # Calculate acceleration efficiency
        if self._calc_acceleration_efficiency and (self._received_charge or self._acceleration_loss_fraction is None):
            self._calc_acceleration_efficiency = False
            self._calc_acceleration_loss_fraction()

        # Calculate ejection efficiency
        if self._calc_ejection_efficiency and (self._received_charge or self._ejection_loss_fraction is None):
            self._calc_ejection_efficiency = False
            self._set_kickex('on')
            self._calc_ejection_loss_fraction()
            self._set_kickex('off')


    def _reset(self, message1='reset', message2='', c='white', a=None):
        self._beam_charge  = beam_charge.BeamCharge(nr_bunches = self.nr_bunches)
        self._beam_dump(message1,message2,c,a)

        # Shift accelerator and record names to start in the injection point
        accelerator        = self.model_module.create_accelerator()
        injection_point    = pyaccel.lattice.find_indices(accelerator, 'fam_name', 'sept_in')[0]
        self._accelerator  = pyaccel.lattice.shift(accelerator, start = injection_point)
        self._all_pvs      = utils.shift_record_names(self._accelerator, self._all_pvs)

        if TRACK6D:
            pyaccel.tracking.set6dtracking(self._accelerator)

        self._ext_point    = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'sept_ex')[0]
        self._kickin_idx   = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'kick_in')
        self._kickex_idx   = pyaccel.lattice.find_indices(self._accelerator, 'fam_name', 'kick_ex')
        self._set_vacuum_chamber()

        self._state_deprecated = True
        self._update_state()

        # Initial values of timing pvs
        self._ti_kickinj_enabled = 1
        self._ti_kickinj_delay = 0
        self._ti_kickex_enabled = 1
        self._ti_kickex_delay = 0
        self._ti_kickex_inc = 0
        self._ti_rampps_enabled = 1
        self._ti_rampps_delay = 0

    def _beam_dump(self, message1='panic', message2='', c='white', a=None):
        super()._beam_dump(message1=message1, message2=message2, c=c, a=a)
        self._acceleration_loss_fraction = None
        self._ejection_loss_fraction = None

    def _beam_accelerate(self):
        efficiency = 1.0 - self._acceleration_loss_fraction
        final_charge = self._beam_charge.value
        return efficiency

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

        _dict = self._injection_parameters
        _dict.update(self._get_vacuum_chamber())
        _dict.update(self._get_coordinate_system_parameters())
        self._injection_loss_fraction = injection.calc_charge_loss_fraction_in_ring(self._accelerator, **_dict)

    def _calc_acceleration_loss_fraction(self):
        self._log('calc', 'acceleration efficiency  for '+self.model_module.lattice_version)
        self._acceleration_loss_fraction = 0.0

    def _calc_ejection_loss_fraction(self):
        if self._twiss is None: return
        self._log('calc', 'ejection efficiency  for '+self.model_module.lattice_version)

        accelerator = self._accelerator[self._kickex_idx[0]:self._ext_point+1]
        ejection_parameters = self._get_equilibrium_at_maximum_energy()
        _dict = {}
        _dict.update(ejection_parameters)
        _dict.update(self._get_vacuum_chamber(init_idx=self._kickex_idx[0], final_idx=self._ext_point+1))
        self._ejection_loss_fraction, twiss, *_ = injection.calc_charge_loss_fraction_in_line(accelerator,
            init_twiss=self._twiss[self._kickex_idx[0]], **_dict)

        args_dict = {}
        args_dict.update(ejection_parameters)
        args_dict['init_twiss'] = twiss[-1].make_dict() # picklable object
        self._send_parameters_to_downstream_accelerator(args_dict)

    def _injection(self, charge=None):
        if charge is None: return

        self._log(message1 = 'cycle', message2 = '-- '+self.prefix+' --')
        self._log(message1 = 'cycle', message2 = 'beam injection in {0:s}: {1:.5f} nC'.format(self.prefix, sum(charge)*1e9))

        if not self._ti_kickinj_enabled: charge = [0.0]
        efficiency = self._beam_inject(charge=charge)
        if not self._ti_kickinj_enabled: efficiency = 0
        self._log(message1='cycle', message2='beam injection in {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*efficiency))

        efficiency = self._beam_accelerate()
        self._log(message1='cycle', message2='beam acceleration at {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*efficiency))

        final_charge, efficiency = self._beam_eject()
        if not self._ti_kickex_enabled: final_charge, efficiency = ([0.0], 0)
        self._log(message1='cycle', message2='beam ejection from {0:s}: {1:.2f}% efficiency'.format(self.prefix, 100*efficiency))
        self._send_charge_to_downstream_accelerator({'charge' : final_charge})
