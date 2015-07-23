
import os
import math
import numpy
import pyaccel
import mathphys
import va.utils as utils
from va.model import Model, UNDEF_VALUE


class TLineModel(Model):

    def __init__(self, model_module, all_pvs=None, log_func=utils.log):

        super().__init__(model_module=model_module, all_pvs=all_pvs, log_func=log_func)
        self.reset('start')
        self._init_magnets_and_power_supplies()

    # --- methods implementing response of model to get requests

    def get_pv_static(self, pv_name):
        # process global parameters
        if '-BPM-' in pv_name:
            charge = self._beam_charge.total_value
            idx = self._get_elements_indices(pv_name)
            if 'FAM-X' in pv_name:
                if self._orbit is None or charge == 0.0: return [UNDEF_VALUE]*len(idx)
                return self._orbit[0,idx]
            elif 'FAM-Y' in pv_name:
                if self._orbit is None or charge == 0.0: return [UNDEF_VALUE]*len(idx)
                return self._orbit[2,idx]
            else:
                if self._orbit is None or charge == 0.0: return [UNDEF_VALUE]*2
        elif 'PS-' in pv_name:
            return self._power_supplies[pv_name].current
        elif 'PU-' in pv_name:
            return self._power_supplies[pv_name].current
        else:
            return None

    # --- methods implementing response of model to set requests

    def set_pv(self, pv_name, value):
        if self.set_pv_magnets(pv_name, value): return
        if self.set_pv_fake(pv_name, value): return

    def set_pv_magnets(self, pv_name, value):
        ps = self._power_supplies[pv_name]
        prev_value = ps.current
        if value != prev_value:
            ps.current = value
            self._state_deprecated = True
        return True

    # --- methods that help updating the model state

    def update_state(self, force=False):
        if force or self._state_deprecated:  # we need to check deprecation of other models on which tline depends
            parms = self._get_parameters_from_upstream_accelerator()
            if parms is not None:
                init_twiss = parms['twiss_at_entrance']
                emittance = parms['emittance']
                energy_spread = parms['energy_spread']
                global_coupling = parms['global_coupling']
                self._calc_orbit(init_twiss)
                self._calc_linear_optics(init_twiss)
                self._calc_beam_size(emittance, energy_spread, global_coupling)
                self._calc_loss_fraction()
            self._state_deprecated = False

    def reset(self, message1='reset', message2='', c='white', a=None):
        if self._all_pvs is None:
            self._record_names = self._model_module.record_names.get_record_names()
        else:
            self._record_names = self._all_pvs
        self._accelerator = self._model_module.create_accelerator()
        self._beam_charge  = utils.BeamCharge()
        self._orbit = None
        self._twiss = None
        self._loss_fraction = 0.0
        if not message2:
            message2 = self._model_module.lattice_version
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        self._state_deprecated = False

    def beam_dump(self, message1='panic', message2='', c='white', a=None):
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        self._state_deprecated = True
        self._beam_charge.dump()
        self._orbit = None

    def beam_inject(self, charge, message1='inject', message2 = '', c='white', a=None):
        if message1:
            self._log(message1, message2, c=c, a=a)
        self._beam_charge.inject(charge)
        return self._beam_charge.value

    def beam_transport(self, charge):
        self.update_state()
        charge = self.beam_inject(charge, message1='')
        efficiency = 1.0 - self._loss_fraction
        self._log(message1 = 'cycle', message2 = '  beam transport at {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency))
        charge = [charge_bunch * efficiency for charge_bunch in charge]
        self._beam_charge.dump()
        return charge, efficiency

    # --- auxilliary methods

    def _get_twiss(self, index):
        self.update_state()
        if isinstance(index, str):
            if index == 'end':
                return self._twiss[-1]
            elif index == 'begin':
                return self._twiss[0]
        else:
            return self._twiss[index]

    def _get_parameters_from_upstream_accelerator(self):
        """Return initial Twiss parameters to be tracked"""
        return None

    def _calc_orbit(self, init_twiss):
        if init_twiss is None: return
        init_pos = init_twiss.fixed_point
        try:
            self._log('calc', 'orbit for '+self._model_module.lattice_version)
            self._orbit, *_ = pyaccel.tracking.linepass(self._accelerator, init_pos, indices = 'closed')
        except pyaccel.tracking.TrackingException:
            # beam is lost
            self.beam_dump('panic', 'BEAM LOST: orbit does not exist', c='red')

    def _calc_linear_optics(self, init_twiss):
        if init_twiss is None: return
        try:
            self._log('calc', 'linear optics for '+self._model_module.lattice_version)
            self._twiss, *_ = pyaccel.optics.calc_twiss(self._accelerator, init_twiss=init_twiss, indices='closed')
        except pyaccel.tracking.TrackingException:
            self.beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')

    def _calc_beam_size(self, natural_emittance, natural_energy_spread, coupling):
        if self._twiss is None: return
        betax, etax, betay, etay = pyaccel.optics.get_twiss(self._twiss, ('betax','etax','betay','etay'))
        emitx = natural_emittance * 1 / (1 + coupling)
        emity = natural_emittance * coupling / (1 + coupling)
        self._sigmax = numpy.sqrt(betax * emitx + (etax * natural_energy_spread)**2)
        self._sigmay = numpy.sqrt(betay * emity + (etax * natural_energy_spread)**2)

    def _get_elements_indices(self, pv_name):
        """Get flattened indices of element in the model"""
        data = self._record_names[pv_name]
        indices = []
        for key in data.keys():
            idx = mathphys.utils.flatten(data[key])
            indices.extend(idx)
        return indices

    def _init_magnets_and_power_supplies(self):
        accelerator = self._accelerator
        accelerator_data = self._model_module.accelerator_data
        magnet_names = self._model_module.record_names.get_magnet_names()
        magnet_names.update(self._model_module.record_names.get_pulsed_magnet_names())
        family_mapping = self._model_module.family_mapping
        excitation_curve_mapping = self._model_module.excitation_curves.get_excitation_curve_mapping()
        _, ps2magnet = self._model_module.power_supplies.get_magnet_mapping()

        self._magnets = dict()
        for magnet_name in magnet_names.keys():
            excitation_curve = excitation_curve_mapping[magnet_name]
            try:
                filename = os.path.join(accelerator_data['dirs']['excitation_curves'], excitation_curve)
            except:
                filename = os.path.join(accelerator_data['dirs']['excitation_curves'], 'not_found')

            family, indices = magnet_names[magnet_name].popitem()
            indices = indices[0]
            family_type = family_mapping[family]
            if family_type == 'dipole':
                magnet = utils.DipoleMagnet(accelerator, indices, filename)
            elif family_type == 'quadrupole':
                magnet = utils.QuadrupoleMagnet(accelerator, indices, filename)
            elif family_type == 'sextupole':
                magnet = utils.SextupoleMagnet(accelerator, indices, filename)
            elif family_type in ('slow_horizontal_corrector', 'fast_horizontal_corrector', 'horizontal_corrector'):
                magnet = utils.HorizontalCorrectorMagnet(accelerator, indices, filename)
            elif family_type in ('slow_vertical_corrector', 'fast_vertical_corrector', 'vertical_corrector'):
                magnet = utils.VerticalCorrectorMagnet(accelerator, indices, filename)
            elif family_type == 'skew_quadrupole':
                magnet = utils.SkewQuadrupoleMagnet(accelerator, indices, filename)
            elif family_type in ('septum'):
                magnet = utils.SeptumMagnet(accelerator, indices, filename)
            else:
                magnet = None

            if magnet is not None:
                self._magnets[magnet_name] = magnet

        # Set initial current values
        self._power_supplies = dict()
        for ps_name in ps2magnet.keys():
            magnets = set()
            for magnet_name in ps2magnet[ps_name]:
                if magnet_name in self._magnets:
                    magnets.add(self._magnets[magnet_name])
            if '-FAM' in ps_name:
                power_supply = utils.FamilyPowerSupply(magnets)
            else:
                power_supply = utils.IndividualPowerSupply(magnets)
            self._power_supplies[ps_name] = power_supply

    def _calc_loss_fraction(self):
        if self._orbit is None: return 0.0
        self._log('calc', 'loss fraction for '+self._model_module.lattice_version)

        h_vc = self._hmax - self._hmin
        v_vc = self._vmax - self._vmin
        rx, ry = self._orbit[[0,2],:]
        xlim_inf, xlim_sup = rx - self._hmin, self._hmax - rx
        ylim_inf, ylim_sup = ry - self._vmin, self._vmax - ry
        xlim_inf[xlim_inf < 0] = 0
        xlim_sup[xlim_sup < 0] = 0
        ylim_inf[ylim_inf < 0] = 0
        ylim_sup[ylim_sup < 0] = 0
        xlim_inf[xlim_inf > h_vc] = 0
        xlim_sup[xlim_sup > h_vc] = 0
        ylim_inf[ylim_inf > v_vc] = 0
        ylim_sup[ylim_sup > v_vc] = 0
        min_xfrac_inf = numpy.amin(xlim_inf/self._sigmax)
        min_xfrac_sup = numpy.amin(xlim_sup/self._sigmax)
        min_yfrac_inf = numpy.amin(ylim_inf/self._sigmay)
        min_yfrac_sup = numpy.amin(ylim_sup/self._sigmay)
        sqrt2 = math.sqrt(2)
        x_surviving_fraction = 0.5*math.erf(min_xfrac_inf/sqrt2) + \
                               0.5*math.erf(min_xfrac_sup/sqrt2)
        y_surviving_fraction = 0.5*math.erf(min_yfrac_inf/sqrt2) + \
                               0.5*math.erf(min_yfrac_sup/sqrt2)
        surviving_fraction = x_surviving_fraction * y_surviving_fraction

        self._loss_fraction = 1.0 - surviving_fraction
