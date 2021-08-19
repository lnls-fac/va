#!/usr/local/bin/python-sirius -u

import os as _os
import argparse as _argparse
from siriuspy.envars import VACA_PREFIX
LAB_PREFIX = _os.environ.get('LAB_PREFIX', 'sirius')


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
args = parser.parse_args()

# --- set environment LAB_PREFIX so that pvs subpackge can load correct models
_os.environ['LAB_PREFIX'] = args.lab
import va.server

# --- run VA
va.server.run(args.lab, args.prefix, only_orbit=args.orbit, print_pvs=args.pvs)
