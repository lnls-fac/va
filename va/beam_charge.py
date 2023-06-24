
import time
import math
import numpy


class BeamCharge:

    def __init__(self, charge = 0.0,
                 nr_bunches = 1,
                 elastic_lifetime = float("inf"),
                 inelastic_lifetime = float("inf"),
                 quantum_lifetime = float("inf"),
                 touschek_coefficient = 0.0):

        # Convert args to lists, if not yet; get nr_bunches
        self._charge =  (charge/nr_bunches) * numpy.ones(nr_bunches)
        self._elastic_lifetime = elastic_lifetime
        self._inelastic_lifetime = inelastic_lifetime
        self._quantum_lifetime = quantum_lifetime
        self._touschek_coefficient = touschek_coefficient
        self._timestamp = time.time()
        self._accumulated_value = 0.0

    def get_lifetimes(self):
        return [self._elastic_lifetime, self._inelastic_lifetime, self._quantum_lifetime, self._touschek_coefficient]

    def set_lifetimes(self, lifetime):
        total_charge = self.total_value # updates values
        self._elastic_lifetime = lifetime.lifetime_elastic
        self._inelastic_lifetime = lifetime.lifetime_inelastic
        self._quantum_lifetime = lifetime.lifetime_quantum
        self._touschek_coefficient = lifetime.lossrate_touschek / total_charge if total_charge > 0 else 0

    @property
    def nr_bunches(self):
        return len(self._charge)

    @property
    def loss_rate(self):
        charge = self.value # updates values
        sp_loss_rate = self._elastic_lifetime**(-1) + self._inelastic_lifetime**(-1) + self._quantum_lifetime**(-1)
        current_loss_rate = sp_loss_rate + self._touschek_coefficient * self._charge
        return current_loss_rate, charge

    @property
    def lifetime(self):
        self.value
        n = len(self._charge)
        current_loss_rate, *_ = self.loss_rate
        b_lifetime  = [float("inf") if bunch_loss_rate==0.0 else 1.0/bunch_loss_rate for bunch_loss_rate in current_loss_rate]
        return numpy.array(b_lifetime)

    @property
    def total_lifetime(self):
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
    def value(self):
        single_particle_lifetime = self._calc_single_particle_lifetime()

        # updates bunch charges
        prev_total_value = sum(self._charge)
        t0, t1 = self._timestamp, time.time()
        expf = math.exp(-(t1-t0)/single_particle_lifetime)
        if single_particle_lifetime == float('inf'):
            touf = 0
        else:
            touf = self._touschek_coefficient*single_particle_lifetime*(1.0 - expf) * self._charge
        self._charge = expf * self._charge / (1.0 + touf)

        new_total_value = sum(self._charge)
        # update accumulated charge
        self._accumulated_value = self._accumulated_value + math.fabs((new_total_value - prev_total_value))*(t1-t0)

        self._timestamp = t1  # updates timestamp
        return self._charge.copy()

    @property
    def total_value(self):
        current_charge = self.value
        return sum(current_charge)

    def accumulated_charge(self, time_interval):
        self.value
        return (self._accumulated_value/time_interval)

    def current(self, time_interval):
        charges = self.value
        currents = charges / time_interval
        return currents

    def inject(self, delta_charge):
        current_charge = self.value
        total_nr_bunches = len(current_charge)
        for i in range(len(delta_charge)):
            idx = i % total_nr_bunches
            self._charge[idx] += delta_charge[i]

    def eject(self):
        ejected_charge = self.value
        self.dump()
        return ejected_charge

    def dump(self):
        self._charge = 0 * self._charge
        self._timestamp = time.time()

    def _calc_single_particle_lifetime(self):
        single_particle_loss_rate = self._elastic_lifetime**(-1) + self._inelastic_lifetime**(-1)
        if single_particle_loss_rate == 0:
            single_particle_lifetime = float('inf')
        else:
            single_particle_lifetime = 1.0 / single_particle_loss_rate
        return single_particle_lifetime
