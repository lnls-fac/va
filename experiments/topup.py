#!/usr/bin/env python3

import datetime
import epics
import time
import lnls
import signal
import sys

_TOPUP_CURRENT     = 300 # [mA]
_MAX_CURRENT_DECAY = 5.0 # [%]
_TIME_INTERVAL     = 2.0 # [s]
_DELTA_CURRENT     = 0.1 # [mA]
_RAMP_CYCLE_FREQ   = 2.0 # [Hz]

# pvs that control injection process
si_current = epics.pv.PV('SIDI-CURRENT')
va_inject  = epics.pv.PV('VA-SIFK-INJECT')

def signal_handler(signum, frame):
    if timer1.is_running():
        timer1.stop()
    sys.exit()

def inject():
    timer1.stop()
    value = si_current.get()
    delta_current = _TOPUP_CURRENT - value
    if abs(delta_current)/_TOPUP_CURRENT >= _MAX_CURRENT_DECAY/100.0:
        while value < _TOPUP_CURRENT:
            va_inject.put(delta_current)
            time.sleep(1.0/_RAMP_CYCLE_FREQ)
    timer1.start()


timer1 = lnls.Timer(_TIME_INTERVAL,inject, signal_handler=signal_handler)

if __name__ == '__main__':
    timer1.start()
    signal.pause()
