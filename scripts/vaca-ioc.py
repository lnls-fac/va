#!/usr/local/bin/python-sirius -u

import os as _os
import argparse as _argparse
from siriuspy.envars import VACA_PREFIX
LAB_PREFIX = _os.environ.get('LAB_PREFIX', 'sirius')
VACA_UPDATE = _os.environ.get('VACA_UPDATE', '5.0')


# --- process arguments
parser = _argparse.ArgumentParser(description="Run VACA.")
parser.add_argument('-o', '--orbit', action='store_true', default=False,
                    help="If present simulate only orbit")
parser.add_argument('-f', '--pvs', action='store_true', default=False,
                    help="If present print pvs in file")
parser.add_argument('-p', "--prefix", type=str, default=VACA_PREFIX,
                    help="prefix to be used")
parser.add_argument('-l', "--lab", type=str, default=LAB_PREFIX,
                    help="laboratory name of accelerators")
parser.add_argument('-u', "--update", type=str, default=VACA_UPDATE,
                    help="update frequency of fluctuating PV values [Hz]")
args = parser.parse_args()

# --- set environment LAB_PREFIX so that pvs subpackge can load correct models
_os.environ['LAB_PREFIX'] = args.lab
_os.environ['VACA_UPDATE'] = args.update
import va.server

# --- run VA
va.server.run(args.lab, args.prefix, only_orbit=args.orbit, print_pvs=args.pvs)
