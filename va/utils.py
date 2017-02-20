
import time
import datetime
from termcolor import colored
import pyaccel
import mathphys
import va


UNDEF_VALUE = 0.0
PREFIX_LEN = 2

# Interprocess communication commands - move here


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


def process_and_wait_interval(processing_function, interval):
    start_time = time.time()
    processing_function()
    _wait_interval(start_time, interval)


def _wait_interval(start_time, interval):
    delta_t = time.time() - start_time
    if 0 < delta_t < interval:
        time.sleep(interval - delta_t)
