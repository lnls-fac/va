
import math


class PowerSupply(object):

    def __init__(self, magnets, model):
        """Gets and sets current [A]
        Connected magnets are processed after current is set.
        """
        self._model = model
        self._magnets = magnets
        for m in magnets:
            m.add_power_supply(self)

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = value
        for m in self._magnets:
            m.process()


class FamilyPowerSupply(PowerSupply):

    def __init__(self, magnets, model, current=None):
        """Initialises current from average integrated field in magnets"""
        super().__init__(magnets, model=model)
        if (current is None) and (len(magnets) > 0):
            total_current = 0.0
            n = 0
            for m in magnets:
                total_current += m.current
                n += 1
            self._current = total_current/n
        else:
            self._current = 0.0

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = value
        for m in self._magnets:
            m.process()
        # Change strengths of other magnets when accelerator energy is changed
        if isinstance(list(self._magnets)[0], DipoleMagnet):
            all_power_supplies = self._model._power_supplies.values()
            for ps in all_power_supplies:
                if not isinstance(list(ps._magnets)[0], DipoleMagnet):
                    ps.current = ps._current


class IndividualPowerSupply(PowerSupply):

    def __init__(self, magnets, model, current = None):
        super().__init__(magnets, model=model)
        if len(magnets) > 1:
            raise Exception('Individual Power Supply')
        elif (current is None) and (len(magnets) > 0):
            magnet = list(magnets)[0]
            total_current = magnet.current
            power_supplies = magnet._power_supplies.difference({self})
            ps_current = 0.0
            for ps in power_supplies:
                ps_current += ps.current
            self._current = (total_current - ps_current) if math.fabs((total_current - ps_current))> 1e-10 else 0.0
        else:
            self._current = 0.0
