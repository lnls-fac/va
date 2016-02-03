
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
        self._charge = [charge/nr_bunches] * nr_bunches
        self._elastic_lifetime = elastic_lifetime
        self._inelastic_lifetime = inelastic_lifetime
        self._quantum_lifetime = quantum_lifetime
        self._touschek_coefficient = touschek_coefficient
        self._timestamp = time.time()
        self._accumulated_value = 0.0

    def get_lifetimes(self):
        return [self._elastic_lifetime, self._inelastic_lifetime, self._quantum_lifetime, self._touschek_coefficient]

    def set_lifetimes(self, elastic=None, inelastic=None, quantum=None, touschek_coefficient=None):
        self.value # updates values
        if elastic is not None: self._elastic_lifetime = elastic
        if inelastic is not None: self._inelastic_lifetime = inelastic
        if quantum is not None: self._quantum_lifetime = quantum
        if touschek_coefficient is not None: self._touschek_coefficient = touschek_coefficient

    @property
    def loss_rate(self):
        charge = self.value # updates values
        current_loss_rate = [self._elastic_lifetime**(-1) + self._inelastic_lifetime**(-1) + self._quantum_lifetime**(-1) + self._touschek_coefficient * charge for charge in self._charge]
        return current_loss_rate, charge

    @property
    def lifetime(self):
        self.value
        n = len(self._charge)
        current_loss_rate, *_ = self.loss_rate
        b_lifetime  = [float("inf") if bunch_loss_rate==0.0 else bunch_loss_rate**(-1) for bunch_loss_rate in current_loss_rate]
        return b_lifetime

    @property
    def total_lifetime(self):
        w, q = self.loss_rate
        q_total = sum(q)
        if q_total != 0.0:
            w_avg = sum([w[i]*q[i] for i in range(len(q))])/sum(q)
        else:
            w_avg = sum(w)/len(w)
        return 1.0/w_avg

    @property
    def value(self):
        single_particle_loss_rate = self._elastic_lifetime**(-1) + self._inelastic_lifetime**(-1)
        if single_particle_loss_rate == 0:
            single_particle_lifetime = float('inf')
        else:
            single_particle_lifetime = 1.0 / single_particle_loss_rate
        # updates bunch charges
        prev_total_value = sum(self._charge)
        t0, t1 = self._timestamp, time.time()
        expf = math.exp(-(t1-t0)/single_particle_lifetime)
        touf = numpy.multiply(self._charge, self._touschek_coefficient*single_particle_lifetime*(1.0 - expf))
        new_value = expf*numpy.divide(self._charge, (1.0 + touf))
        for i in range(len(self._charge)):
            if not math.isnan(new_value[i]):
                self._charge[i] = new_value[i]
        new_total_value = sum(self._charge)
        self._accumulated_value = self._accumulated_value + math.fabs((new_total_value - prev_total_value))*(t1-t0)
        # updates timestamp
        self._timestamp = t1
        return self._charge[:]

    @property
    def total_value(self):
        current_charge = self.value
        return sum(current_charge)

    def accumulated_charge(self, time_interval):
        self.value
        return (self._accumulated_value/time_interval)

    def current(self, time_interval):
        charges = self.value
        currents = [bunch_charge/time_interval for bunch_charge in charges]
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
        self._charge = [0] * len(self._charge)
        self._timestamp = time.time()
