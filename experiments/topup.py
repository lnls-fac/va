#!/usr/bin/env python3

import datetime
import epics
import time
import lnls
import signal
import sys

_TOPUP_CURRENT = 300 # [mA]

def signal_handler(signum, frame):
    timer1.stop()
    sys.exit()

def inject():
    value = si_current.get()
    delta_current = _TOPUP_CURRENT - value
    dv = (_TOPUP_CURRENT - value)/_TOPUP_CURRENT
    if abs(delta_current)/_TOPUP_CURRENT >= 0.05:
        va_inject.put(delta_current)



si_current = epics.pv.PV('SIDI-CURRENT')
va_inject  = epics.pv.PV('VA-SIFK-INJECT')
timer1 = lnls.Timer(2,inject, signal_handler=signal_handler)



if __name__ == '__main__':
    timer1.start()
    signal.pause()
qq
