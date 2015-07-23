
import pyaccel
import va.utils as utils
from va.accelerator_model import AcceleratorModel

class TLineModel(AcceleratorModel):

    def __init__(self, all_pvs=None, log_func=utils.log):
        super().__init__(all_pvs=all_pvs, log_func=log_func)

    # --- methods that help updating the model state

    def update_state(self, force=False):
        if force or self._state_deprecated:
            self._calc_transport_loss_fraction()
            self._injection_loss_fraction = 0.0
            self._ejection_loss_fraction = 0.0
            self._state_deprecated = False

    def beam_dump(self, message1='panic', message2='', c='white', a=None):
        super().beam_dump(message1=message1, message2=message2, c=c, a=a)
        self._transport_loss_fraction = None

    def beam_transport(self, charge):
        self.update_state()
        efficiency = 1.0 - self._transport_loss_fraction
        #self._log(message1 = 'cycle', message2 = '  beam transport at {0:s}: {1:.2f}% efficiency'.format(self._model_module.lattice_version, 100*efficiency))
        charge = [charge_bunch * efficiency for charge_bunch in charge]
        self._beam_charge.dump()
        return charge, efficiency

    # --- auxilliary methods

    def _calc_transport_loss_fraction(self):
        if self._model_module.lattice_version.startswith('LI'):
            self._transport_loss_fraction = 0.0
        else:
            self._log('calc', 'transport efficiency  for '+self._model_module.lattice_version)
            args_dict = self._get_parameters_from_upstream_accelerator()
            args_dict['init_twiss'] = args_dict.pop('twiss_at_entrance')
            args_dict.update(self._get_vacuum_chamber())
            args_dict.update(self._get_coordinate_system_parameters())
            self._transport_loss_fraction, self._twiss, self._m66, self._transfer_matrices, self._orbit = \
                utils.charge_loss_fraction_line(self._accelerator, **args_dict)

    # def _calc_orbit(self, init_twiss):
    #     if init_twiss is None: return
    #     init_pos = init_twiss.fixed_point
    #     try:
    #         self._log('calc', 'orbit for '+self._model_module.lattice_version)
    #         self._orbit, *_ = pyaccel.tracking.linepass(self._accelerator, init_pos, indices = 'open')
    #     except pyaccel.tracking.TrackingException:
    #         # beam is lost
    #         self.beam_dump('panic', 'BEAM LOST: orbit does not exist', c='red')
    #
    # def _calc_linear_optics(self, init_twiss):
    #     if init_twiss is None: return
    #     try:
    #         self._log('calc', 'linear optics for '+self._model_module.lattice_version)
    #         self._twiss, *_ = pyaccel.optics.calc_twiss(self._accelerator, init_twiss=init_twiss, indices='open')
    #     except pyaccel.tracking.TrackingException:
    #         self.beam_dump('panic', 'BEAM LOST: unstable linear optics', c='red')
    #
    # def _calc_beam_size(self, natural_emittance, natural_energy_spread, coupling):
    #     if self._twiss is None: return
    #     betax, etax, betay, etay = pyaccel.optics.get_twiss(self._twiss, ('betax','etax','betay','etay'))
    #     emitx = natural_emittance * 1 / (1 + coupling)
    #     emity = natural_emittance * coupling / (1 + coupling)
    #     self._sigmax = numpy.sqrt(betax * emitx + (etax * natural_energy_spread)**2)
    #     self._sigmay = numpy.sqrt(betay * emity + (etax * natural_energy_spread)**2)
