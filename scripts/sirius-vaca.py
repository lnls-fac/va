#!/usr/bin/env python3

import sys
import va.server


print("This is a modified script")
print("And this is the develop version")
if len(sys.argv) > 1:
    prefix = sys.argv[1]
else:
    prefix = "VA-"

va.server.run(prefix)
