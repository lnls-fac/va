#!/usr/local/bin/python-sirius -u

import argparse as _argparse
from siriuspy.envars import vaca_prefix as prefix

parser = _argparse.ArgumentParser(description="Run VACA.")
parser.add_argument('-o', '--orbit', action='store_true', default=False,
                    help="If present simulate only orbit")
parser.add_argument('-f', '--pvs', action='store_true', default=True,
                    help="If present print pvs in file")
parser.add_argument('-p', "--prefix", type=str, default='',
                    help="prefix to be used")
args = parser.parse_args()

import va.server
va.server.run(args.prefix or prefix, only_orbit=args.orbit, print_pvs=args.pvs)
