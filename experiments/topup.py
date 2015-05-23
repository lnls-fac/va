#!/usr/bin/env python3

import datetime
import epics
import time
import lnls
import signal
import sys

_TOPUP_CURRENT     = 300       # [mA]
_MAX_CURRENT_DECAY = 0.5       # [%]
_TIME_INTERVAL     = 2.0       # [s]
_RAMP_CYCLE_FREQ   = 2.0       # [Hz]

max_current = _TOPUP_CURRENT
min_current = _TOPUP_CURRENT * (1.0 - _MAX_CURRENT_DECAY/100.0)

# pvs that control injection process
si_current = epics.pv.PV('VA-SIDI-CURRENT')
ti_cycle   = epics.pv.PV('VA-TI-CYCLE')

si_current.wait_for_connection()
ti_cycle.wait_for_connection()
is_injecting = False

def signal_handler(signum, frame):
    if timer1.is_running():
        timer1.stop()
    sys.exit()

def check_inject():
    global is_injecting
    if is_injecting: return
    while si_current.get() < min_current:
        is_injecting = True
        while si_current.get() < max_current:
            ti_cycle.put(1)
            time.sleep(1.0/_RAMP_CYCLE_FREQ)   # cycle intercal
    is_injecting = False


timer1 = lnls.Timer(_TIME_INTERVAL, check_inject, signal_handler=signal_handler)

if __name__ == '__main__':
    timer1.start()
    signal.pause()
