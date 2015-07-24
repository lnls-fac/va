
import time
import pyaccel
import va.utils as utils

class TimingModel(object):

    def __init__(self, all_pvs=None, log_func=utils.log):
        self._driver = None # this will be set latter by Driver
        self._log = log_func
        self._all_pvs = all_pvs
        self.reset('start')

    # --- methods implementing response of model to get requests

    def get_pv(self, pv_name):
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

    def set_pv(self, pv_name, value):
        if 'CYCLE' in pv_name:
            self._cycle = value
            self._beam_inject()
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

    def all_models_defined_ack(self):
        rfrequency = self._driver.si_model.get_pv('SIRF-FREQUENCY')
        self._bo_kickex_inc = 1.0 / rfrequency

    def update_state(self):
        pass

    def reset(self, message1='reset', message2='', c='white', a=None):
        if self._all_pvs is None:
            self._record_names = self._model_module.record_names.get_record_names()
        else:
            self._record_names = self._all_pvs
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

    def _beam_inject(self):

        def add_time(t):
            t.append(time.time())
        def get_time(t):
            return 1000*(t[-1]-t[-2])
        def get_total_time(t):
            return 1000*(t[-1]-t[0])

        if not self._cycle: return

        t = []
        add_time(t)
        self._log(message1='cycle', message2='TI starting injection')

        # LI
        # ==
        model = self._driver.li_model
        self._log(message1='cycle', message2=' -- LI --', c='white')
        # create charge from electron gun
        if model._single_bunch_mode:
            charge = [model._model_module.single_bunch_charge]
        else:
            charge = [model._model_module.multi_bunch_charge/model._nr_bunches]*model._nr_bunches
        initial_charge = charge
        self._log(message1='cycle', message2=' electron gun providing charge: {0:.5f} nC'.format(sum(charge)*1e9), c='white')
        # transport through linac
        charge = self._transport_to_line(charge, model, t, add_time, get_time)
        model.notify_driver()

        # TB
        # ==
        model = self._driver.tb_model
        self._log(message1='cycle', message2=' -- TB --', c='white')
        self._log(message1='cycle', message2=' beam injection in {0:s}: {1:.5f} nC'.format(model._prefix, sum(charge)*1e9), c='white')
        charge = self._transport_to_line(charge, model, t, add_time, get_time)
        model.notify_driver()

        # BO
        # ==
        model = self._driver.bo_model
        self._log(message1='cycle', message2=' -- BO --', c='white')
        self._log(message1='cycle', message2=' beam injection in {0:s}: {1:.5f} nC'.format(model._model_module.lattice_version, sum(charge)*1e9), c='white')
        # injection into booster
        charge = charge if self._bo_kickin_on else [0]
        injection_efficiency = model.beam_inject(charge)
        efficiency = injection_efficiency if self._bo_kickin_on else 0
        add_time(t)
        self._log(message1='cycle', message2=' beam injection in {0:s}: {1:.2f}% efficiency, {2:.0f} ms'.format(model._prefix, 100*efficiency, get_time(t)), c='white')
        # acceleration through booster
        acceleration_efficiency = model.beam_accelerate()
        add_time(t)
        self._log(message1='cycle', message2=' beam acceleration at {0:s}: {1:.2f}% efficiency, {2:.0f} ms'.format(model._prefix, 100*acceleration_efficiency, get_time(t)))
        # ejection from booster
        new_charge, ejection_efficiency = model.beam_eject()
        charge, efficiency = (new_charge, ejection_efficiency) if self._bo_kickex_on else ([0], 0)
        add_time(t)
        self._log(message1 = 'cycle', message2 = ' beam ejection from {0:s}: {1:.2f}% efficiency, {2:.0f} ms'.format(model._prefix, 100*efficiency, get_time(t)), c='white')
        model.notify_driver()

        # TS
        # ==
        model = self._driver.ts_model
        self._log(message1 = 'cycle', message2 = ' -- TS --', c='white')
        self._log(message1 = 'cycle', message2 = ' beam injection in {0:s}: {1:.5f} nC'.format(model._prefix, sum(charge)*1e9), c='white')
        charge = self._transport_to_line(charge, model, t, add_time, get_time)
        model.notify_driver()

        # SI
        # ==
        model = self._driver.si_model
        self._log(message1 = 'cycle', message2 = ' -- SI --', c='white')
        self._log(message1 = 'cycle', message2 = ' beam injection in {0:s}: {1:.5f} nC'.format(model._prefix, sum(charge)*1e9), c='white')
        #   injection into sirius
        if self._si_kickin_on:
            final_charge = self._incoming_bunch_injected_in_si(charge)
            efficiency = model.beam_inject(final_charge)
        else:
            final_charge, efficiency = [0], 0
        add_time(t)
        self._log(message1 = 'cycle', message2 = ' beam injection in {0:s}: {1:.2f}% efficiency'.format(model._prefix, 100*efficiency), c='white')
        self._log(message1 = 'cycle', message2 = ' beam injection at {0:s}: {1:.0f} ms'.format(model._prefix, get_time(t)))
        model.notify_driver()

        # prepares internal data for next cycle
        self._set_delay_next_cycle()
        total_efficiency = sum(final_charge)/sum(initial_charge)
        add_time(t)
        self._log(message1 = 'cycle', message2 = ' ::{0:.2f}% efficiency overall, total time: {1:.0f} ms.'.format(100*total_efficiency,get_total_time(t)))

    # --- auxilliary methods

    def _transport_to_line(self, charge, model, t, add_time, get_time):
        new_charge, efficiency = model.beam_transport(charge)
        add_time(t)
        message1 = 'cycle'
        message2 = ' beam transport at {0:s}: {1:.2f}% efficiency, {2:.0f} ms'.format(model._prefix, 100*efficiency, get_time(t))
        self._log(message1 = message1, message2 = message2)
        return new_charge

    def _set_delay_next_cycle(self):
        self._bo_kickex_delay += self._bo_kickex_inc
        self._driver.setParam('TI-BO-KICKEX-DELAY', self._bo_kickex_delay)

    def _incoming_bunch_injected_in_si(self, charge):
        rffrequency = pyaccel.optics.get_rf_frequency(self._driver.si_model._accelerator)
        bunch_offset = round(self._bo_kickex_delay * rffrequency)
        harmonic_number = self._driver.si_model._accelerator.harmonic_number
        bunch_charge = [0.0] * harmonic_number
        for i in range(len(charge)):
            n = (i + bunch_offset) % harmonic_number
            bunch_charge[n] += charge[i]
        return bunch_charge

    #
    # def _beam_inject(self):
    #
    #     def add_time(t):
    #         t.append(time.time())
    #     def get_time(t):
    #         return 1000*(t[-1]-t[-2])
    #     def get_total_time(t):
    #         return 1000*(t[-1]-t[0])
    #
    #     if not self._cycle: return
    #
    #     t = []
    #     add_time(t)
    #     self._log(message1='cycle', message2='TI starting injection')
    #
    #     # LI
    #     # ==
    #     model = self._driver.li_model
    #     self._log(message1='cycle', message2='  -- LI --', c='white')
    #     # create charge from electron gun
    #     if model._single_bunch_mode:
    #         charge = [model._model_module.single_bunch_charge]
    #     else:
    #         charge = [model._model_module.multi_bunch_charge]*model._nr_bunches
    #     initial_charge = charge
    #     self._log(message1='cycle', message2='  electron gun providing charge: {0:.5f} nC'.format(sum(charge)*1e9), c='white')
    #     # transport through linac
    #     new_charge, efficiency = model.beam_transport(charge)
    #     model.notify_driver()
    #     add_time(t)
    #     self._log(message1='cycle', message2='  beam transport at {0:s}: {1:.2f}% efficiency, {2:.0f} ms'.format(model._model_module.lattice_version, 100*efficiency, get_time(t)))
    #     charge = new_charge
    #
    #     # TB
    #     # ==
    #     model = self._driver.tb_model
    #     self._log(message1='cycle', message2='  -- TB --', c='white')
    #     self._log(message1='cycle', message2='  beam injection in {0:s}: {1:.5f} nC'.format(model._model_module.lattice_version, sum(charge)*1e9), c='white')
    #     add_time(t)
    #     new_charge, efficiency = model.beam_transport(charge)
    #     #self._driver.tb_model.notify_driver()
    #     add_time(t)
    #     self._log(message1='cycle', message2='  beam transport at {0:s}: {1:.2f}% efficiency, {2:.0f} ms'.format(model._model_module.lattice_version, 100*efficiency, get_time(t)))
    #     charge = new_charge
    #
    #     # BO
    #     # ==
    #     model = self._driver.bo_model
    #     self._log(message1='cycle', message2='  -- BO --', c='white')
    #     # injection into booster
    #     self._log(message1='cycle', message2='  beam injection in {0:s}: {1:.5f} nC'.format(model._model_module.lattice_version, sum(charge)*1e9), c='white')
    #     add_time(t)
    #     charge = charge if self._bo_kickin_on else 0.0
    #     injection_efficiency = model.beam_inject(charge)
    #     add_time(t)
    #     self._log(message1='cycle', message2='  beam injection in {0:s}: {1:.2f}% efficiency, {2:.0f} ms'.format(model._model_module.lattice_version, 100*injection_efficiency, get_time(t)), c='white')
    #
    #     # acceleration through booster
    #     add_time(t)
    #     acceleration_efficiency = model.beam_accelerate()
    #     add_time(t)
    #     self._log(message1='cycle', message2='  beam acceleration at {0:s}: {1:.2f}% efficiency, {2:.0f} ms'.format(model._model_module.lattice_version, 100*acceleration_efficiency, get_time(t)))
    #
    #     # ejection from booster
    #     add_time(t)
    #     new_charge, ejection_efficiency = model.beam_eject()
    #     charge, efficiency = (new_charge, ejection_efficiency) if self._bo_kickex_on else (0.0, 0.0)
    #     add_time(t)
    #     self._log(message1 = 'cycle', message2 = '  beam ejection from {0:s}: {1:.2f}% efficiency, {2:.0f} ms'.format(model._model_module.lattice_version, 100*efficiency, get_time(t)), c='white')
    #     # self._driver.bo_model.notify_driver()
    #
    #     # TS
    #     # ==
    #     model = self._driver.ts_model
    #     self._log(message1 = 'cycle', message2 = '  -- TS --', c='white')
    #     charge = self._incoming_bunch_injected_in_si(charge) # adds delay
    #     self._log(message1 = 'cycle', message2 = '  beam injection in {0:s}: {1:.5f} nC'.format(model._model_module.lattice_version, sum(charge)*1e9), c='white')
    #     new_charge, efficiency = model.beam_transport(charge)
    #     #self._driver.ts_model.notify_driver()
    #     add_time(t)
    #     self._log(message1 = 'cycle', message2 = '  beam transport at {0:s}: {1:.2f}% efficiency, {2:.0f} ms'.format(model._model_module.lattice_version, 100*efficiency, get_time(t)))
    #     charge = new_charge
    #
    #     # SI
    #     # ==
    #     model = self._driver.si_model
    #     self._log(message1 = 'cycle', message2 = '  -- SI --', c='white')
    #     #   injection into sirius
    #     self._log(message1 = 'cycle', message2 = '  beam injection in {0:s}: {1:.5f} nC'.format(model._model_module.lattice_version, sum(charge)*1e9), c='white')
    #     add_time(t)
    #     if self._si_kickin_on:
    #         self._incoming_bunch_injected_in_si(charge)
    #         final_charge = charge
    #         efficiency = model.beam_inject(charge)
    #     else:
    #         final_charge = 0
    #         charge, efficiency = [0], 0
    #         self._log(message1 = 'cycle', message2 = '  beam injection in {0:s}: {1:.2f}% efficiency'.format(model._model_module.lattice_version, 0.0), c='white')
    #     add_time(t)
    #     self._log(message1 = 'cycle', message2 = '  beam injection at {0:s}: {1:.0f} ms'.format(model._model_module.lattice_version, get_time(t)))
    #     self._driver.si_model.notify_driver()
    #
    #
    #     # prepares internal data for next cycle
    #     self._set_delay_next_cycle()
    #
    #     total_efficiency = sum(final_charge)/sum(initial_charge)
    #     add_time(t)
    #     self._log(message1 = 'cycle', message2 = '  :: {0:.2f}% efficiency overall, total time: {1:.0f} ms.'.format(100*total_efficiency,get_total_time(t)))
