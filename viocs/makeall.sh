#!/bin/bash

declare -a viocsprojs=("si_bpms" "si_current" "si_ps" "si_tune" "si_rf" "si_beamsize" "bo_bpms" "bo_current" "bo_ps" "bo_rf" "tb_ps" "tb_bpms" "ts_ps" "ts_bpms")

for ioc in "${viocsprojs[@]}"
do
  chmod -R a+r $ioc
  cd $ioc
  make
  chmod a+rx $ioc"App/src/O.linux-x86_64/"$ioc
  chmod a+rx iocBoot/ioc$ioc/st.cmd
  cd ..
done
