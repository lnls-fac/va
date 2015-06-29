
from va.model import Model, UNDEF_VALUE
import va.utils as utils
import mathphys
import pyaccel
import numpy
import math


class TLineModel(Model):

    def __init__(self, model_module, all_pvs=None, log_func=utils.log):

        super().__init__(model_module=model_module, all_pvs=all_pvs, log_func=log_func)
        self.reset('start')

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
        elif 'PS-CH' in pv_name:
            idx = self._get_elements_indices(pv_name) # vector with indices of corrector segments
            kickfield = 'hkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'hkick_polynom'
            kicks = pyaccel.lattice.get_attribute(self._accelerator, kickfield, idx)
            value = sum(kicks)
            return value
        elif 'PS-CV' in pv_name:
            idx = self._get_elements_indices(pv_name)
            kickfield = 'vkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'vkick_polynom'
            kicks = pyaccel.lattice.get_attribute(self._accelerator, kickfield, idx)
            value = sum(kicks)
            return value
        elif 'PS-Q' in pv_name:
            idx = self._get_elements_indices(pv_name)
            value = self._accelerator[idx[0]].polynom_b[1]
            return value
        elif 'PS-BEND-' in pv_name or 'PU-SEP' in pv_name:
            idx = self._get_elements_indices(pv_name)
            value = 0
            for i in idx:
                value += self._accelerator[i].polynom_b[0]*self._accelerator[i].length
                value += self._accelerator[i].angle
            return value
        else:
            return None

    # --- methods implementing response of model to set requests

    def set_pv(self, pv_name, value):
        if self.set_pv_correctors(pv_name, value): return
        if self.set_pv_quadrupoles(pv_name, value): return
        if self.set_pv_bends(pv_name, value): return
        if self.set_pv_fake(pv_name, value): return

    def set_pv_correctors(self, pv_name, value):
        if 'PS-CH' in pv_name:
            idx = self._get_elements_indices(pv_name)
            nr_segs = len(idx)
            kickfield = 'hkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'hkick_polynom'
            prev_value = nr_segs * getattr(self._accelerator[idx[0]], kickfield)
            if value != prev_value:
                pyaccel.lattice.set_attribute(self._accelerator, kickfield, idx, value/nr_segs)
                self._state_deprecated = True
            return True

        if 'PS-CV' in pv_name:
            idx = self._get_elements_indices(pv_name)
            nr_segs = len(idx)
            kickfield = 'vkick' if self._accelerator[idx[0]].pass_method == 'corrector_pass' else 'vkick_polynom'
            prev_value = nr_segs * getattr(self._accelerator[idx[0]], kickfield)
            if value != prev_value:
                pyaccel.lattice.set_attribute(self._accelerator, kickfield, idx, value/nr_segs)
                self._state_deprecated = True
            return True
        return False  # [pv is not a corrector]

    def set_pv_quadrupoles(self, pv_name, value):
        if 'PS-Q' in pv_name:
            idx = self._get_elements_indices(pv_name)
            idx2 = idx
            while not isinstance(idx2,int):
                idx2 = idx2[0]
            prev_value = self._accelerator[idx2].polynom_b[1]
            if value != prev_value:
                if isinstance(idx,int): idx = [idx]
                for i in idx:
                    self._accelerator[i].polynom_b[1] = value
                self._state_deprecated = True
            return True
        return False # [pv is not a quadrupole]

    def set_pv_bends(self, pv_name, value):
        if 'PS-BEND-' in pv_name or 'PU-SEP' in pv_name:
            idx = self._get_elements_indices(pv_name)
            prev_value = 0
            for i in idx:
                prev_value += self._accelerator[i].polynom_b[0]*self._accelerator[i].length
                prev_value += self._accelerator[i].angle
            if value != prev_value:
                for i in idx:
                    angle_i = self._accelerator[i].angle
                    new_angle_i = angle_i *(value/prev_value)
                    self._accelerator[i].polynom_b[0] = (new_angle_i - angle_i)/self._accelerator[i].length
                self._state_deprecated = True
            return True
        return False

    # --- methods that help updating the model state

    def update_state(self, force=False):
        if force or self._state_deprecated:  # we need to check deprecation of other models on which tline depends
            #print('tline update_state: ',self._model_module.lattice_version)
            parms = self._get_parameters_from_upstream_accelerator()
            if parms is not None:
                #print(parms)
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
        self._log(message1 = 'cycle', message2 = 'beam transport at {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency))
        charge = [charge_bunch * efficiency for charge_bunch in charge]
        self._beam_charge.dump()
        return charge

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
            self._twiss, *_ = pyaccel.optics.calc_twiss(self._accelerator, init_twiss=init_twiss)

            # propagates Twiss till the end of last element.
            # This expedient is temporary. It should be removed once calc_twiss is augmented to
            # include 'indices' argument with possible 'closed' value.
            aux_acc = self._accelerator[-2:-1]
            aux_acc.append(pyaccel.elements.marker(''))
            twiss, *_ = pyaccel.optics.calc_twiss(aux_acc, init_twiss=self._twiss[-1])
            self._twiss.append(twiss[-1])


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

    def _calc_loss_fraction(self):
        if self._orbit is None: return 0.0
        self._log('calc', 'loss fraction for '+self._model_module.lattice_version)
        n = len(self._accelerator)
        hmax, hmin = numpy.zeros((2,n+1))
        vmax, vmin = numpy.zeros((2,n+1))
        for i in range(n):
            hmax[i] = self._accelerator._accelerator.lattice[i].hmax
            vmax[i] = self._accelerator._accelerator.lattice[i].vmax
            hmin[i] = -hmax[i]
            vmin[i] = -vmax[i]
            fam_name = self._accelerator._accelerator.lattice[i].fam_name
            if fam_name == 'esep':
                hmax[i] = 0.0075 # FIX ME! : extend trackcpp to allow for hmax and hmin?!
            elif fam_name == 'sseb':
                hmax[i] = 0.0015 # FIX ME! : extend trackcpp to allow for hmax and hmin?!
            elif fam_name == 'esef':
                hmax[i] = 0.0015 # FIX ME! : extend trackcpp to allow for hmax and hmin?!
        hmax[-1], hmin[-1] = hmax[-2], hmin[-2]
        vmax[-1], vmin[-1] = vmax[-2], vmin[-2]
        #print(self._model_module.lattice_version)
        rx, ry = self._orbit[[0,2],:]
        xlim_inf, xlim_sup = rx - hmin, hmax - rx
        ylim_inf, ylim_sup = ry - vmin, vmax - ry
        xlim_inf[xlim_inf < 0] = 0
        xlim_sup[xlim_sup < 0] = 0
        ylim_inf[ylim_inf < 0] = 0
        ylim_sup[ylim_sup < 0] = 0

        min_xfrac_inf = numpy.amin(xlim_inf/self._sigmax)
        min_xfrac_sup = numpy.amin(xlim_sup/self._sigmax)
        min_yfrac_inf = numpy.amin(ylim_inf/self._sigmay)
        min_yfrac_sup = numpy.amin(ylim_sup/self._sigmay)

        #print('min_xfrac_inf:', min_xfrac_inf)
        #print('min_xfrac_sup:', min_xfrac_sup)
        #print('min_yfrac_inf:', min_yfrac_inf)
        #print('min_yfrac_sup:', min_yfrac_sup)

        sqrt2 = math.sqrt(2)
        x_surviving_fraction = 0.5*math.erf(min_xfrac_inf/sqrt2) + \
                               0.5*math.erf(min_xfrac_sup/sqrt2)
        y_surviving_fraction = 0.5*math.erf(min_yfrac_inf/sqrt2) + \
                               0.5*math.erf(min_yfrac_sup/sqrt2)
        surviving_fraction = x_surviving_fraction * y_surviving_fraction
        #print(surviving_fraction)
        self._loss_fraction = 1.0 - surviving_fraction
        #return 1.0 - surviving_fraction
