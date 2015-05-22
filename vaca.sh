#!/bin/bash

### This script is supposed to be run at lnls82-linux

export EPICS_CA_AUTO_ADDR_LIST=NO
export EPICS_CA_ADDR_LIST=10.0.21.255

procServ -n server -i ^D^C 23000 $FAC_CODE/va/server.py VA-

