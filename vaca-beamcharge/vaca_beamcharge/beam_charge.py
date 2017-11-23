"""Definition of the BeamCharge class."""
import time
import math
import numpy


class BeamCharge:
    """Beam Charge Class.

    Simulates time-evolution of beam charge and currents given partial
    lifetimes.

    Attributes:
        reference_current -- reference current for Touschek lifetime parameter.
    """

    reference_current = 300e-3  # [A]

    def __init__(self,
                 charge=0.0,
                 nr_bunches=1,
                 period=0.0,
                 lifetime_elastic=float("inf"),
                 lifetime_inelastic=float("inf"),
                 lifetime_quantum=float("inf"),
                 lifetime_touschek_ref=float("inf")):
        """Set inital parameters."""
        # Convert args to lists, if not yet; get nr_bunches
        self._nr_bunches = nr_bunches
        self._period = period
        self._charge = [charge/nr_bunches] * nr_bunches
        self._lifetime_elastic = lifetime_elastic
        self._lifetime_inelastic = lifetime_inelastic
        self._lifetime_quantum = lifetime_quantum
        self._lifetime_touschek_ref = lifetime_touschek_ref
        self._touschek_coefficient = \
            self._calc_touschek_coeff(self._lifetime_touschek_ref)
        self._timestamp = time.time()

    # --- properties ---

    @property
    def period(self):
        """Return time period."""
        return self._period

    @property
    def nr_bunches(self):
        """Number of bunches."""
        return self._nr_bunches

    @property
    def lifetime_elastic(self):
        """Elastic lifetime parameter."""
        return self._lifetime_elastic

    @lifetime_elastic.setter
    def lifetime_elastic(self, value):
        """Set elastic lifetime parameter."""
        self._update()
        self._lifetime_elastic = value

    @property
    def lifetime_inelastic(self):
        """Inelastic lifetime parameter."""
        return self._lifetime_inelastic

    @lifetime_inelastic.setter
    def lifetime_inelastic(self, value):
        """Set inelastic lifetime parameter."""
        self._update()
        self._lifetime_inelastic = value

    @property
    def lifetime_quantum(self):
        """Quatum lifetime parameter."""
        return self._lifetime_quantum

    @lifetime_quantum.setter
    def lifetime_quantum(self, value):
        """Set quantum lifetime parameter."""
        self._update()
        self._lifetime_quantum = value

    @property
    def lifetime_touschek_ref(self):
        """Touchesk lifetime parameter."""
        return self._lifetime_touschek_ref

    @lifetime_touschek_ref.setter
    def lifetime_touschek_ref(self, value):
        """Set Touschek lifetime at reference current parameter."""
        self._update()
        self._lifetime_touschek_ref = value
        self._touschek_coefficient = self._calc_touschek_coeff(value)

    @property
    def lifetime_touschek(self):
        """Touchesk lifetime."""
        current = self.current
        if current == 0:
            return float('inf')
        else:
            return self._lifetime_touschek_ref * \
                   BeamCharge.reference_current / current

    @property
    def loss_rate_BbB(self):
        """Calculate loss rate bunch-by-bunch."""
        charge = self.charge_BbB  # updates values
        current_loss_rate_BbB = [self._lifetime_elastic**(-1) +
                                 self._lifetime_inelastic**(-1) +
                                 self._lifetime_quantum**(-1) +
                                 self._touschek_coefficient * charge
                                 for charge in self._charge]
        return current_loss_rate_BbB, charge

    @property
    def loss_rate(self):
        """Return beam loss rate."""
        return 1.0/self.lifetime

    @property
    def loss_rate_charge(self):
        """Return beam charge loss rate [C/s]."""
        return self.charge/self.lifetime

    @property
    def loss_rate_current(self):
        """Return beam charge loss rate [C/s]."""
        return self.loss_rate_charge/self._period

    @property
    def lifetime_BbB(self):
        """Return lifetime by bunch."""
        # n = len(self.value_BbB)
        current_loss_rate_BbB, *_ = self.loss_rate_BbB
        b_lifetime = [float("inf") if bunch_loss_rate_BbB == 0.0
                      else 1.0/bunch_loss_rate_BbB
                      for bunch_loss_rate_BbB in current_loss_rate_BbB]
        return b_lifetime

    @property
    def lifetime(self):
        """Return total lifetime."""
        w, q = self.loss_rate_BbB
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
    def charge_BbB(self):
        """Return bunch-by-bunch charges."""
        self._update()
        return self._charge[:]

    @property
    def charge(self):
        """Return total charge."""
        current_charge = self.charge_BbB
        return sum(current_charge)

    @property
    def current_BbB(self):
        """Return current by bunch."""
        charges = self.charge_BbB
        currents = [bunch_charge/self._period
                    for bunch_charge in charges]
        return currents

    @property
    def current(self):
        """Return sum of current in all bunches."""
        currents = self.current_BbB
        return sum(currents)

    # --- public methods ---

    def inject(self, delta_charge):
        """Inject a delta charge to all bunches."""
        current_charge = self.charge_BbB
        total_nr_bunches = len(current_charge)
        for i in range(len(delta_charge)):
            idx = i % total_nr_bunches
            self._charge[idx] += delta_charge[i]

    def eject(self):
        """Eject beam charge."""
        ejected_charge = self.charge_BbB
        self.dump()
        return ejected_charge

    def dump(self):
        """Dump beam charge."""
        self._charge = [0] * len(self._charge)
        self._timestamp = time.time()

    # --- private methods ---

    def _update(self):
        single_particle_loss_rate = \
            self._lifetime_elastic**(-1) + self._lifetime_inelastic**(-1)
        if single_particle_loss_rate == 0:
            single_particle_lifetime = float('inf')
        else:
            single_particle_lifetime = 1.0 / single_particle_loss_rate
        # updates bunch charges
        t0, t1 = self._timestamp, time.time()
        expf = math.exp(-(t1-t0)/single_particle_lifetime)
        touf = numpy.multiply(
            self._charge,
            self._touschek_coefficient*single_particle_lifetime*(1.0 - expf))
        new_value = expf*numpy.divide(self._charge, (1.0 + touf))
        for i in range(len(self._charge)):
            if not math.isnan(new_value[i]):
                self._charge[i] = new_value[i]
        # updates timestamp
        self._timestamp = t1

    def _calc_touschek_coeff(self, lifetime):
        if lifetime * self._period == 0:
            return float('inf')
        else:
            return 1.0/(lifetime*BeamCharge.reference_current*self._period)
