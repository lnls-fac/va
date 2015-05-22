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
ti_cycle   = epics.pv.PV('VA-TI-CYCLE')

is_injecting = False

def signal_handler(signum, frame):
    if timer1.is_running():
        timer1.stop()
    sys.exit()

def check_inject():
    global is_injecting
    while not is_injecting and si_current.status and si_current.get() < min_current:
        is_injecting = True
        while s_current.status and si_current.get() < max_current:
            bo_inject.put(BO_DELTA_CURRENT)    # inject in booster
            bo_inject.put(-BO_DELTA_CURRENT)   # eject from booster
            si_inject.put(SI_DELTA_CURRENT)    # inject in sirius
            time.sleep(1.0/_RAMP_CYCLE_FREQ)   # cycle intercal
        is_injecting = False


timer1 = lnls.Timer(_TIME_INTERVAL, check_inject, signal_handler=signal_handler)

if __name__ == '__main__':
    timer1.start()
    signal.pause()
