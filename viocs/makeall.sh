#!/bin/bash

declare -a viocsprojs=("si_bpms" "si_current" "si_lifetime" "si_ps" "si_tune")

for ioc in "${viocsprojs[@]}"
do
  chmod -R a+r $ioc
  cd $ioc
  make
  chmod a+rx $ioc"App/src/O.linux-x86_64/"$ioc
  chmod a+rx iocBoot/ioc$ioc/st.cmd
  cd ..
done
