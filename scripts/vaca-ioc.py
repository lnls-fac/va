#!/usr/local/bin/python-sirius -u

import argparse as _argparse
from siriuspy.envars import VACA_PREFIX

VACA_PREFIX = 'VA-' if VACA_PREFIX == '' else VACA_PREFIX

parser = _argparse.ArgumentParser(description="Run VACA.")
parser.add_argument('-o', '--orbit', action='store_true', default=False,
                    help="If present simulate only orbit")
parser.add_argument('-f', '--pvs', action='store_true', default=False,
                    help="If present print pvs in file")
parser.add_argument('-p', "--prefix", type=str, default='',
                    help="prefix to be used")
parser.add_argument('-l', "--lab", type=str, default='sirius',
                    help="laboratory name of accelerators")

args = parser.parse_args()

import va.server

va.server.run(args.prefix or VACA_PREFIX, only_orbit=args.orbit, print_pvs=args.pvs)
