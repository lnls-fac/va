#!/usr/bin/python3.4

import sys
import va.server
import siriuspy

if len(sys.argv) > 1:
    prefix = sys.argv[1]
else:
    prefix = siriuspy.envars.vaca_prefix

va.server.run(prefix)
