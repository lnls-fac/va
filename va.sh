#!/bin/bash

### This script is supposed to be run at lnls82-linux
### It starts all virtual IOCs using procServ

export EPICS_CA_AUTO_ADDR_LIST=NO
export EPICS_CA_ADDR_LIST=10.0.21.255
VIOCS=$FACCODE/va/viocs
port=23000
declare -a viocsprojs=("si_bpms" "si_current" "si_lifetime" "si_ps" "si_tune")


### guarantees that IOCs are executable by anyone
chmod a+x $FACCODE/va/server.py
for ioc in "${viocsprojs[@]}"
do
    chmod a+x $VIOCS/$ioc/$ioc"App"/src/O.linux-x86_64/$ioc
done

### starts VIOCS
procServ -n server -i ^D^C $port $FACCODE/va/server.py VA-
for ioc in "${viocsprojs[@]}"
do
    port=$((port+1))
    #echo $ioc" "$port
    procServ -n $ioc -i ^D^C $port $VIOCS/$ioc/$ioc"App"/src/O.linux-x86_64/$ioc $VIOCS/$ioc/iocBoot/"ioc"$ioc/st.cmd
done


