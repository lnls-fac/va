#!/bin/bash

### This script is supposed to be run at lnls82-linux

export EPICS_CA_AUTO_ADDR_LIST=NO
export EPICS_CA_ADDR_LIST=10.0.21.255

procServ -n vaca -i ^D^C 23000 $FACCODE/va/server.py VA-
procServ -n si_current -i ^D^C 23001 $FACCODE/va/viocs/si_current/si_currentApp/src/O.linux-x86_64/si_current $FACCODE/va/viocs/si_current/iocBoot/iocsi_current/st.cmd


