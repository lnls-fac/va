import time
import math
import datetime
from termcolor import colored
import va

def print_banner(prefix, si_pv_names, bo_pv_names):

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
    print(r"")



def log(message1='', message2='', c='white', a=None):
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    if a is None: a = []
    strt = colored(st, 'white', attrs=[])
    str1 = colored('{0:<6.6s}'.format(message1), c, attrs=a)
    str2 = colored('{0}'.format(message2), c, attrs=a)
    strt = strt + ': ' + str1 + ' ' + str2
    print(strt)
    #return strt + ': ' + str1 + ' ' + str2

class BeamCharge:

    def __init__(self, charge=None, lifetime = float("inf")):

        # converts args to lists, if not yet. get nr_bunches
        if not charge: charge = [0.0]
        if isinstance(charge, (int,float)):
            charge = [charge]
        if isinstance(lifetime, (int, float)):
            lifetime = [lifetime]
        nr_bunches = max(len(lifetime),len(charge))

        # make sure both charge and lifetime lists have appropriate lens
        if len(charge) == 1:
            if len(lifetime)==1:
                self._charge = charge      # [coulomb]
                self._lifetime = lifetime  # [seconds]
            else:
                self._charge = [charge[0]/nr_bunches] * nr_bunches
                self._lifetime = lifetime
        else:
            if len(lifetime) == 1:
                self._charge = charge
                self._lifetime = [lifetime[0]] * nr_bunches
            else:
                if len(charge) != len(lifetime):
                    raise Excpetion('inconsistent charge and lifetime arguments')

        self._timestamp  = time.time()

    @property
    def lifetime(self):
        return self._lifetime

    @lifetime.setter
    def lifetime(self, value):
        if isinstance(value, (int,float)):
            self._lifetime = [value] * len(self._lifetime)
        else:
            self._lifetime = value

    @property
    def value(self):
        # updates current value
        t0, t1 = self._timestamp, time.time()
        for i in range(len(self._charge)):
            new_value = self._charge[i] * math.exp(-(t1-t0)/self._lifetime[i])
            if not math.isnan(new_value):
                self._charge[i] = new_value
        self._timestamp = t1
        return self._charge

    @property
    def total_value(self):
        current_charge = self.value
        return sum(current_charge)

    @property
    def average_lifetime(self):
        lifetime = self._lifetime
        charges = self.value
        total_charge = sum(charges)
        if total_charge:
            avg_lifetime = sum([(charges[i]/total_charge) * lifetime[i] for i in range(len(lifetime))])
        else:
            avg_lifetime = 0.0
        return avg_lifetime

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
