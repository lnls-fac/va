
import time
import math
import datetime
import numpy
from termcolor import colored
import mathphys
import va

def print_banner(prefix, li_pv_names=None,
                         tb_pv_names=None,
                         bo_pv_names=None,
                         ts_pv_names=None,
                         si_pv_names=None,
                         ti_pv_names=None):

    def c(msg,color=None,attrs=None):
        if not attrs:
            attrs=['bold']
        return colored(msg,color=color,attrs=attrs)

    print(r"")
    print(c(r"         (___)    ",'white') + " | " + c("Virtual Accelerator with Channel Access server"))
    print(c(r"    _____(.oo)    ",'white') + " | " + c("Version {0}".format(va.__version__)))
    print(c(r"  //     ' ",'white')+c("@@     ",'magenta') + " | " + c("LNLS Accelerator Physics Group", attrs=['bold']))
    print(c(r" # \ ,",'white')+c("VACA")+c(" /      ",'white') + " | " + c("Documentation: https://github.com/lnls-fac/va"))
    print(c(" ~~~",'green') + c(r"\\",'white') + c("~~~",'green') + c(r"||",'white')+c("~~~~~  ",'green') + " | " + c("Prefix: {0}".format(prefix), attrs=['bold']))
    print(c(r"    ^^   ^^       ",'white') + " | " + c("Number of SI pvs: {0}".format(len(si_pv_names))))
    print(r"              "+c("\|/ ",'green') + " | " + c("Number of BO pvs: {0}".format(len(bo_pv_names))))
    if li_pv_names is not None:
        print(c(r"                  ",'white') + " | " + c("Number of LI pvs: {0}".format(len(li_pv_names))))
    if ti_pv_names is not None:
        print(c(r"                  ",'white') + " | " + c("Number of TI pvs: {0}".format(len(ti_pv_names))))
    if tb_pv_names is not None:
        print(c(r"                  ",'white') + " | " + c("Number of TB pvs: {0}".format(len(tb_pv_names))))
    if ts_pv_names is not None:
        print(c(r"                  ",'white') + " | " + c("Number of TS pvs: {0}".format(len(ts_pv_names))))
    print(r"")

def log(message1='', message2='', c='white', a=None):
    t0 = time.time()
    st = datetime.datetime.fromtimestamp(t0).strftime('%Y-%m-%d %H:%M:%S')
    st = st + '.{0:03d}'.format(int(1000*(t0-int(t0))))
    if a is None: a = []
    strt = colored(st, 'white', attrs=[])
    str1 = colored('{0:<6.6s}'.format(message1), c, attrs=a)
    str2 = colored('{0}'.format(message2), c, attrs=a)
    strt = strt + ': ' + str1 + ' ' + str2
    print(strt)
    #return strt + ': ' + str1 + ' ' + str2


class BeamCharge:

    def __init__(self, charge = 0.0,
                 nr_bunches = 1,
                 elastic_lifetime = float("inf"),
                 inelastic_lifetime = float("inf"),
                 quantum_lifetime = float("inf"),
                 touschek_coefficient = 0.0):

        # converts args to lists, if not yet. get nr_bunches
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
        for i in range(len(self._charge)):
            expf = math.exp(-(t1-t0)/single_particle_lifetime)
            touf = self._touschek_coefficient * single_particle_lifetime * self._charge[i] * (1.0 - expf)
            #print(touf)
            new_value = self._charge[i] * expf / (1.0 + touf)
            if not math.isnan(new_value):
                self._charge[i] = new_value
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
        nr_bunches = len(current_charge)
        for i in range(len(delta_charge)):
            idx = i % nr_bunches
            self._charge[idx] += delta_charge[i]

    def dump(self):
        self._charge = [0] * len(self._charge)
        self._timestamp = time.time()


class Magnet(object):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Magnet with power supplies

        Reads current from power supplies and sets Accelerator elements fields
        using value converted with excitation curve."""
        self._power_supplies = set()
        self._accelerator = accelerator

        if isinstance(indices, int):
            self._indices = [indices]
        else:
            self._indices = indices

        length = 0.0
        for i in self._indices:
            length += self._accelerator[i].length
        self._length = length

        self._load_excitation_curve(exc_curve_filename)

    def add_power_supply(self, power_supply):
        self._power_supplies.add(power_supply)

    def process(self):
        current = 0.0
        for ps in self._power_supplies:
            current += ps.current
        new_value = numpy.interp(current, self._i, self._f)
        self.value = new_value

    @property
    def value(self):
        return self._get_value()

    @value.setter
    def value(self, integrated_field):
        """Set integrated field

        If element is segmented, all segments are assigned the same polynom
        value.
        """
        self._set_value(integrated_field)

    @property
    def current(self):
        return numpy.interp(self.value, self._f, self._i)

    def _get_value(self):
        v = 0.0
        for i in self._indices:
            polynom = getattr(self._accelerator[i], self._polynom)
            v += polynom[self._polynom_index]*self._accelerator[i].length

        integrated_field = v*self._accelerator.brho
        return integrated_field

    def _set_value(self, integrated_field):
        field = integrated_field/(self._length*self._accelerator.brho)
        for i in self._indices:
            polynom = getattr(self._accelerator[i], self._polynom)
            polynom[self._polynom_index] = field

    def _load_excitation_curve(self, filename):
        try:
            data = numpy.loadtxt(filename)
        except FileNotFoundError:
            # Default conversion table: F = I/2
            data = numpy.array([[-1000, 1000], [-500, 500]]).transpose()
        self._i = data[:, 0]
        self._f = data[:, 1]


class DipoleMagnet(Magnet):

    """Gets and sets beam energy [eV]

    DipoleMagnet is processed differently from other Magnet objects: it
    averages the current over the set of power supplies.
    """

    @property
    def value(self):
        """Get beam energy [eV]"""
        return self._accelerator.energy

    @value.setter
    def value(self, energy):
        """Get beam energy [T·m]"""
        self._accelerator.energy = energy

    def process(self):
        current = 0.0
        n = len(self._power_supplies)
        if n > 0:
            for ps in self._power_supplies:
                current += ps.current
            new_value = numpy.interp(current/n, self._i, self._f)
        else:
            new_value = 0.0

        self.value = new_value


class SeptumMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom = 'polynom_b'
        self._polynom_index = 0

        angle = 0.0
        for i in self._indices:
            angle += self._accelerator[i].angle
        self._angle = angle

    def _get_value(self):
        v = 0.0
        for i in self._indices:
            polynom = getattr(self._accelerator[i], self._polynom)
            v += polynom[self._polynom_index]*self._accelerator[i].length/self._accelerator[i].angle
        energy = (1.0 + v)*self._accelerator.energy
        return energy

    def _set_value(self, energy):
        for i in self._indices:
            polynom = getattr(self._accelerator[i], self._polynom)
            polynom[self._polynom_index] = (self._angle/self._length)*(energy/self._accelerator.energy - 1.0)

class QuadrupoleMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom = 'polynom_b'
        self._polynom_index = 1

class SextupoleMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T/m]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom = 'polynom_b'
        self._polynom_index = 2


class CorrectorMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T·m]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom_index = 0
        self._pass_method = self._accelerator[self._indices[0]].pass_method

    @property
    def value(self):
        """Get integrated field [T·m]"""
        if self._pass_method != 'corrector_pass':
            return self._get_value()
        else:
            v = 0.0
            for i in self._indices:
                v += getattr(self._accelerator[i], self._kick)
            integrated_field = v*self._accelerator.brho
            return integrated_field

    @value.setter
    def value(self, integrated_field):
        """Set integrated field [T·m]

        If element is segmented, all segments are assigned the same B.
        """
        if self._pass_method != 'corrector_pass':
            self._set_value(integrated_field)
        else:
            total_kick = integrated_field/self._accelerator.brho
            for i in self._indices:
                kick = total_kick*self._accelerator[i].length/self._length
                setattr(self._accelerator[i], self._kick, kick)


class HorizontalCorrectorMagnet(CorrectorMagnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T·m]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._kick = 'hkick'
        self._polynom = 'polynom_b'


class VerticalCorrectorMagnet(CorrectorMagnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T·m]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._kick = 'vkick'
        self._polynom = 'polynom_a'


class SkewQuadrupoleMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom = 'polynom_a'
        self._polynom_index = 1


class PowerSupply(object):

    def __init__(self, magnets):
        """Gets and sets current [A]

        Connected magnets are processed after current is set.
        """
        self._magnets = magnets
        # self._current = current
        for magnet in magnets:
            magnet.add_power_supply(self)

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = value
        for magnet in self._magnets:
            magnet.process()


class FamilyPowerSupply(PowerSupply):

    def __init__(self, magnets, current=None):
        """Initialises current from average integrated field in magnets"""
        super().__init__(magnets)
        if (current is None) and (len(magnets) > 0):
            total_current = 0.0
            n = 0
            for magnet in magnets:
                total_current += magnet.current
                n += 1
            self._current = total_current/n
        else:
            self._current = 0.0


class IndividualPowerSupply(PowerSupply):

    def __init__(self, magnets, current = None):
        super().__init__(magnets)
        if (current is None) and (len(magnets) > 0):
            total_current = 0.0
            n = 0
            for magnet in magnets:
                total_current += magnet.current
                n += 1
            self._current = total_current/n
        else:
            self._current = 0.0
