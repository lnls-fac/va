import time
import math
import datetime
from termcolor import colored
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


    def set_lifetime(elastic=None, inelastic=None, quantum=None, touschek_coefficient=None):
        self.value # updates values
        if elastic: self._elastic_lifetime = elastic_lifetime
        if inelastic: self._inelastic_lifetime = inelastic_lifetime
        if quantum: self._quantum_lifetime = quantum_lifetime
        if touschek_coefficient: self._touschek_coefficient = touschek_coefficient

    @property
    def lifetime(self):
        self.value # updates values
        n = len(self._charge)
        scattering_rate = [self._elastic_lifetime**(-1) + self._inelastic_lifetime**(-1) + self._quantum_lifetime**(-1) + self._touschek_coefficient * charge for charge in self._charge]
        b_lifetime  = [float("inf") if bunch_scattering_rate==0.0 else bunch_scattering_rate**(-1) for bunch_scattering_rate in scattering_rate]
        return b_lifetime

    @property
    def value(self):
        single_particle_scatt_ratio = self._elastic_lifetime**(-1) + self._inelastic_lifetime**(-1)
        if single_particle_scatt_ratio == 0:
            single_particle_lifetime = float('inf')
        else:
            single_particle_lifetime = 1.0 / single_particle_scatt_ratio
        # updates bunch charges
        t0, t1 = self._timestamp, time.time()
        for i in range(len(self._charge)):
            expf = math.exp(-(t1-t0)/single_particle_lifetime)
            touf = self._touschek_coefficient * single_particle_lifetime * self._charge[i] * (1.0 - expf)
            #print(touf)
            new_value = self._charge[i] * expf / (1.0 + touf)
            if not math.isnan(new_value):
                self._charge[i] = new_value
        # updates timestamp
        self._timestamp = t1
        return self._charge

    @property
    def total_value(self):
        current_charge = self.value
        return sum(current_charge)

    def current(self, time_interval):
        charges = self.value
        currents = [bunch_charge/time_interval for bunch_charge in charges]
        return currents

    def inject(self, delta_charge):
        if isinstance(delta_charge, (int, float)):
            delta_charge = [delta_charge/len(self._charge)] * len(self._charge)
        current_charge = self.value
        self._charge = [current_charge[i]+delta_charge[i] for i in range(len(delta_charge))]

    def dump(self):
        self._charge = [0] * len(self._charge)
        self._timestamp = time.time()
