#!/usr/bin/python3

import sys
import va.server
import siriuspy

prefix = siriuspy.envars.vaca_prefix
only_orbit = False
if len(sys.argv) > 1:
    only_orbit = sys.argv[1].lower().endswith('true')
if len(sys.argv) > 2:
    only_orbit = sys.argv[1].lower().endswith('true')
    prefix = sys.argv[2]

va.server.run(prefix, only_orbit=only_orbit)
