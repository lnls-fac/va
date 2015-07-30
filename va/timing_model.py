
import time
import sirius
from . import model


class TimingModel(model.Model):

    def __init__(self, pipe, interval):
        super().__init__(pipe, interval)
        self._reset('start', self.model_module.lattice_version)
        self._init_sp_pv_values()

    # --- methods implementing response of model to get requests

    def _get_pv(self, pv_name):
        if 'CYCLE' in pv_name:
            return self._cycle
        elif 'BO-KICKIN-ENABLED' in pv_name:
            return self._bo_kickin_on
        elif 'BO-KICKIN-DELAY' in pv_name:
            return self._bo_kickin_delay
        elif 'BO-KICKEX-ENABLED' in pv_name:
            return self._bo_kickex_on
        elif 'BO-KICKEX-DELAY' in pv_name:
            return self._bo_kickex_delay
        elif 'SI-KICKIN-ENABLED' in pv_name:
            return self._si_kickin_on
        elif 'SI-KICKIN-DELAY' in pv_name:
            return self._si_kickin_delay
        elif 'TI-DELAY' in pv_name:
            return self._delay
        elif 'TI-DELAY-INC' in pv_name:
            return self._delay_inc
        else:
            return None

    def _get_pv(self, pv_name):
        if 'CYCLE' in pv_name:
            return self._cycle
        elif 'BO-KICKIN-ENABLED' in pv_name:
            return self._bo_kickin_on
        elif 'BO-KICKIN-DELAY' in pv_name:
            return self._bo_kickin_delay
        elif 'BO-KICKEX-ENABLED' in pv_name:
            return self._bo_kickex_on
        elif 'BO-KICKEX-DELAY' in pv_name:
            return self._bo_kickex_delay
        elif 'SI-KICKIN-ENABLED' in pv_name:
            return self._si_kickin_on
        elif 'SI-KICKIN-DELAY' in pv_name:
            return self._si_kickin_delay
        elif 'TI-DELAY' in pv_name:
            return self._delay
        elif 'TI-DELAY-INC' in pv_name:
            return self._delay_inc
        else:
            return None

    # --- methods implementing response of model to set requests

    def _set_pv(self, pv_name, value):
        if 'CYCLE' in pv_name:
            self._cycle = value
            self._pipe.send(('s', (pv_name, 0)))
            self._set_delay_next_cycle()
            self._log(message1='cycle', message2='TI starting injection')
            self._send_syncronism_signal('LI')
            self._cycle = 0
        elif 'BO-KICKIN-ENABLED' in pv_name:
            self._bo_kickin_on = value
            self._state_deprecated = True
        elif 'BO-KICKIN-DELAY' in pv_name:
            self._bo_kickin_delay = value
            self._state_deprecated = True
        elif 'BO-KICKEX-ENABLED' in pv_name:
            self._bo_kickex_on = value
            self._state_deprecated = True
        elif 'BO-KICKEX-DELAY' in pv_name:
            self._bo_kickex_delay = value
            self._state_deprecated = True
        elif 'SI-KICKIN-ENABLED' in pv_name:
            self._si_kickin_on = value
            self._state_deprecated = True
        elif 'SI-KICKIN-DELAY' in pv_name:
            self._si_kickin_delay = value
            self._state_deprecated = True
        elif 'TI-DELAY' in pv_name:
            self._delay = value
            self._state_deprecated = True
        elif 'TI-DELAY-INC' in pv_name:
            self._delay_inc = value
            self._state_deprecated = True
        return None

    # --- methods that help updating the model state

    def _update_state(self, force=False):
        if force or self._state_deprecated:
            self._send_pv_value()
            self._state_deprecated = False

    def _init_sp_pv_values(self):
        sp_pv_list = []
        for pv in self._all_pvs.keys():
            value = self._get_pv(pv)
            sp_pv_list.append((pv,value))
        self._pipe.send(('sp', sp_pv_list ))

    def _receive_pv_value(self, pv_name, value):
        if 'SIRF-FREQUENCY' in pv_name:
            self._si_rf_frequency = value
            self._delay_inc += 1.0 / self._si_rf_frequency
            self._pipe.send(('s', ('TI-DELAY-INC', self._delay_inc)))
            self._state_deprecated = True
        elif 'LIPA-MODE' in pv_name:
            if not self._si_rf_frequency: return
            self._li_single_bunch_mode = value
            if not self._li_single_bunch_mode:
                self._delay_inc += (1.0/self._si_rf_frequency )*self._li_nr_bunches
                self._pipe.send(('s', ('TI-DELAY-INC', self._delay_inc)))
                self._state_deprecated = True

    def _send_pv_value(self):
        for pv_name in self._all_pvs:
            if 'BO' in pv_name:
                self._pipe.send(('g', ('BO', pv_name)))
            elif 'SI' in pv_name or 'DELAY':
                self._pipe.send(('g', ('SI', pv_name)))

    def _reset(self, message1='reset', message2='', c='white', a=None):
        if not message2:
            message2 = self._model_module.lattice_version
        if message1 or message2:
            self._log(message1, message2, c=c, a=a)
        self._cycle = 0
        self._delay = 0
        self._delay_inc = 0
        self._bo_kickin_on = 1
        self._bo_kickin_delay = 0
        self._bo_kickex_on = 1
        self._bo_kickex_delay = 0
        self._bo_kickex_inc = 0
        self._si_kickin_on = 1
        self._si_kickin_delay = 0
        self._li_single_bunch_mode = None
        self._si_rf_frequency = None
        self._state_deprecated = True

    # --- auxilliary methods

    def _send_syncronism_signal(self, prefix=None):
        if prefix is None: return
        elif prefix == 'LI':
            self._pipe.send(('p', (prefix, 'receive_syncronism_signal', {})))

    def _set_delay_next_cycle(self):
        self._delay += self._delay_inc
        self._pipe.send(('s', ('TI-DELAY', self._delay)))
        self._state_deprecated = True
