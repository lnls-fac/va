#!/usr/local/bin/python-sirius

import time
import argparse as _argparse
import epics

DEFAULT_TIMEOUT = 10.0
DEFAULT_PRINT_OK = False


def read_pv_names(filename):
    with open(filename, 'r') as fp:
        pvs = fp.read().splitlines()
    return pvs

def get_disconnected(pvobjs):
    not_connected = list()
    for pvname, pv in pvobjs.items():
        if not pv.connected:
            not_connected.append(pvname)
    return not_connected

    
def check_pv_list(filename, timeout=DEFAULT_TIMEOUT, print_ok=DEFAULT_PRINT_OK):

    # read pvs from file
    pvs = read_pv_names(filename)
    pvobjs = {pvname:epics.get_pv(pvname, timeout=None) for pvname in pvs}

    # check PVs
    t0 = time.time()
    while time.time() < t0 + timeout:
        disconnected = get_disconnected(pvobjs)
        print('disconnected PVs: {}/{}'.format(len(disconnected), len(pvs)))
        time.sleep(0.5)
    
    # print disconnected
    disconnected = get_disconnected(pvobjs)
    for pvname in disconnected:
        print(pvname)

    


parser = _argparse.ArgumentParser(description="Check PVs for connection.")
parser.add_argument('-ok', "--print_ok", action='store_true', default=DEFAULT_PRINT_OK,
                    help="If present print PV names connecting")
parser.add_argument('-t', "--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help="Connection timeout")
parser.add_argument('-f', "--file", type=str, default=DEFAULT_TIMEOUT, required=True,
                    help="File with PV names to be checked")
args = parser.parse_args()

check_pv_list(args.file, args.timeout, args.print_ok)

