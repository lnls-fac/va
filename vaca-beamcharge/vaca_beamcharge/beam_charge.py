"""Definition of the BeamCharge class."""
import time
import math
import numpy


class BeamCharge:
    """Calculates charge drop."""

    def __init__(self, charge=0.0,
                 nr_bunches=1,
                 time_interval=0.0,
                 elastic_lifetime=float("inf"),
                 inelastic_lifetime=float("inf"),
                 quantum_lifetime=float("inf"),
                 touschek_lifetime=float("inf")):
        """Set inital parameters."""
        # Convert args to lists, if not yet; get nr_bunches
        self._nr_bunches = nr_bunches
        self._time_interval = time_interval
        self._charge = [charge/nr_bunches] * nr_bunches
        self._elastic_lifetime = elastic_lifetime
        self._inelastic_lifetime = inelastic_lifetime
        self._quantum_lifetime = quantum_lifetime
        self._touschek_lifetime = touschek_lifetime
        self._touschek_coefficient = \
            self._conv_touschek_lifetime(self._touschek_lifetime)
        self._timestamp = time.time()
        self._accumulated_value = 0.0

    def get_lifetimes(self):
        """Return lifetimes."""
        return [self._elastic_lifetime, self._inelastic_lifetime,
                self._quantum_lifetime, self._touschek_lifetime]

    def set_lifetimes(self, elastic=None, inelastic=None, quantum=None,
                      touschek=None):
        """Set lifetime parameters."""
        self.value  # updates values
        if elastic is not None:
            self._elastic_lifetime = elastic
        if inelastic is not None:
            self._inelastic_lifetime = inelastic
        if quantum is not None:
            self._quantum_lifetime = quantum
        if touschek is not None:
            self._touschek_lifetime = touschek
            self._touschek_coefficient = \
                self._conv_touschek_lifetime(self._touschek_lifetime)

    @property
    def nr_bunches(self):
        """Number of bunche."""
        return self._nr_bunches

    @property
    def elastic_lifetime(self):
        """Elastic lifetime parameter."""
        return self._elastic_lifetime

    @elastic_lifetime.setter
    def elastic_lifetime(self, value):
        self._elastic_lifetime = value

    @property
    def inelastic_lifetime(self):
        """Inelastic lifetime parameter."""
        return self._inelastic_lifetime

    @inelastic_lifetime.setter
    def inelastic_lifetime(self, value):
        self._inelastic_lifetime = value

    @property
    def quantum_lifetime(self):
        """Quatum lifetime parameter."""
        return self._quantum_lifetime

    @quantum_lifetime.setter
    def quantum_lifetime(self, value):
        self._quantum_lifetime = value

    @property
    def touschek_lifetime(self):
        """Touchesk lifetime parameter."""
        return self._touschek_lifetime

    @touschek_lifetime.setter
    def touschek_lifetime(self, value):
        self._touschek_lifetime = value
        self._touschek_coefficient = self._conv_touschek_lifetime(value)

    @property
    def loss_rate(self):
        """Calculate loss rate by bunch."""
        charge = self.value_BbB  # updates values
        current_loss_rate = [self._elastic_lifetime**(-1) +
                             self._inelastic_lifetime**(-1) +
                             self._quantum_lifetime**(-1) +
                             self._touschek_coefficient * charge
                             for charge in self._charge]
        return current_loss_rate, charge

    @property
    def lifetime_BbB(self):
        """Return lifetime by bunch."""
        # n = len(self.value_BbB)
        current_loss_rate, *_ = self.loss_rate
        b_lifetime = [float("inf") if bunch_loss_rate == 0.0
                      else 1.0/bunch_loss_rate
                      for bunch_loss_rate in current_loss_rate]
        return b_lifetime

    @property
    def lifetime_total(self):
        """Return total lifetime."""
        w, q = self.loss_rate
        q_total = sum(q)
        if q_total != 0.0:
            w_avg = sum([w[i]*q[i] for i in range(len(q))])/sum(q)
        else:
            w_avg = sum(w)/len(w)
        if w_avg:
            tlt = 1.0/w_avg
        else:
            tlt = float('inf')
        return tlt

    @property
    def value_BbB(self):
        """Retrun vector of charge by bunch."""
        print(self._touschek_coefficient)
        single_particle_loss_rate = \
            self._elastic_lifetime**(-1) + self._inelastic_lifetime**(-1)
        if single_particle_loss_rate == 0:
            single_particle_lifetime = float('inf')
        else:
            single_particle_lifetime = 1.0 / single_particle_loss_rate
        # updates bunch charges
        prev_total_value = sum(self._charge)
        t0, t1 = self._timestamp, time.time()
        expf = math.exp(-(t1-t0)/single_particle_lifetime)
        touf = numpy.multiply(
            self._charge,
            self._touschek_coefficient*single_particle_lifetime*(1.0 - expf))
        new_value = expf*numpy.divide(self._charge, (1.0 + touf))
        for i in range(len(self._charge)):
            if not math.isnan(new_value[i]):
                self._charge[i] = new_value[i]
        new_total_value = sum(self._charge)
        self._accumulated_value = self._accumulated_value + \
            math.fabs((new_total_value - prev_total_value))*(t1-t0)
        # updates timestamp
        self._timestamp = t1
        return self._charge[:]

    @property
    def value(self):
        """Return total charge."""
        current_charge = self.value_BbB
        return sum(current_charge)

    def accumulated_charge(self):
        """Accumulated charge."""
        self.value_BbB
        return (self._accumulated_value/self._time_interval)

    def current_BbB(self):
        """Return current by bunch."""
        charges = self.value_BbB
        currents = [bunch_charge/self._time_interval
                    for bunch_charge in charges]
        return currents

    def current(self):
        """Return sum of current in all bunches."""
        currents = self.current_BbB()
        return sum(currents)

    def inject(self, delta_charge):
        """Inject a delta charge to all bunches."""
        current_charge = self.value_BbB
        total_nr_bunches = len(current_charge)
        for i in range(len(delta_charge)):
            idx = i % total_nr_bunches
            self._charge[idx] += delta_charge[i]

    def eject(self):
        """Eject."""
        ejected_charge = self.value_BbB
        self.dump()
        return ejected_charge

    def dump(self):
        """Dump."""
        self._charge = [0] * len(self._charge)
        self._timestamp = time.time()

    def _conv_touschek_lifetime(self, lifetime):
        try:
            return 1/(lifetime*300e-3*self._time_interval)
        except ZeroDivisionError:
            return float("inf")
