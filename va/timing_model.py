
from . import model


class TimingModel(model.Model):

    def __init__(self, pipe, interval):
        super().__init__(pipe, interval)
        self._reset('start', self.model_module.lattice_version)

    # --- methods implementing response of model to get requests

    def _get_pv(self, pv_name):
        if 'CYCLE' in pv_name:
            return self._cycle
        elif 'BO-KICKIN-ON' in pv_name:
            return self._bo_kickin_on
        elif 'BO-KICKIN-DELAY' in pv_name:
            return self._bo_kickin_delay
        elif 'BO-KICKEX-ON' in pv_name:
            return self._bo_kickex_on
        elif 'BO-KICKEX-DELAY' in pv_name:
            return self._bo_kickex_delay
        elif 'BO-KICKEX-INC' in pv_name:
            return self._bo_kickex_inc
        elif 'SI-KICKIN-ON' in pv_name:
            return self._si_kickin_on
        elif 'SI-KICKIN-DELAY' in pv_name:
            return self._si_kickin_delay
        elif 'SI-KICKIN-INC' in pv_name:
            return self._si_kickin_inc
        else:
            return None

    # --- methods implementing response of model to set requests

    def _set_pv(self, pv_name, value):
        if 'CYCLE' in pv_name:
            self._cycle = value
            self.beam_inject()
            self._cycle = 0
            self._driver.setParam(pv_name, self._cycle)
        elif 'BO-KICKIN-ON' in pv_name:
            self._bo_kickin_on = value
        elif 'BO-KICKIN-DELAY' in pv_name:
            self._bo_kickin_delay = value
        elif 'BO-KICKEX-ON' in pv_name:
            self._bo_kickex_on = value
        elif 'BO-KICKEX-DELAY' in pv_name:
            self._bo_kickex_delay = value
        elif 'SI-KICKIN-ON' in pv_name:
            self._si_kickin_on = value
        elif 'SI-KICKIN-DELAY' in pv_name:
            self._si_kickin_delay = value
        elif 'SI-KICKIN-INC' in pv_name:
            self._si_kickin_inc = value
        return None

    # --- methods that help updating the model state

    def _reset(self, message1='reset', message2='', c='white', a=None):
        if not message2:
            message2 = self._model_module.lattice_version
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        self._cycle = 0
        self._bo_kickin_on = 1
        self._bo_kickin_delay = 0
        self._bo_kickex_on = 1
        self._bo_kickex_delay = 0
        self._bo_kickex_inc = 0
        self._si_kickin_on = 1
        self._si_kickin_delay = 0
