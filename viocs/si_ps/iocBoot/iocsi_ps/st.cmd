#!../../bin/linux-x86_64/si_ps

## You may have to change si_ps to something else
## everywhere it appears in this file

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/si_ps.dbd"
si_ps_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords("db/common.db")
dbLoadTemplate("db/family.substitutions")
dbLoadTemplate("db/ch.substitutions")
dbLoadTemplate("db/cv.substitutions")
dbLoadTemplate("db/fch.substitutions")
dbLoadTemplate("db/fcv.substitutions")
dbLoadTemplate("db/qs.substitutions")
dbLoadTemplate("db/qfa.substitutions")
dbLoadTemplate("db/qda.substitutions")
dbLoadTemplate("db/qfb.substitutions")
dbLoadTemplate("db/qdb1.substitutions")
dbLoadTemplate("db/qdb2.substitutions")
dbLoadTemplate("db/qfp.substitutions")
dbLoadTemplate("db/qdp1.substitutions")
dbLoadTemplate("db/qdp2.substitutions")
dbLoadTemplate("db/q1.substitutions")
dbLoadTemplate("db/q2.substitutions")
dbLoadTemplate("db/q3.substitutions")
dbLoadTemplate("db/q4.substitutions")
dbLoadTemplate("db/sda0.substitutions")
dbLoadTemplate("db/sda1.substitutions")
dbLoadTemplate("db/sda2.substitutions")
dbLoadTemplate("db/sda3.substitutions")
dbLoadTemplate("db/sfa0.substitutions")
dbLoadTemplate("db/sfa1.substitutions")
dbLoadTemplate("db/sfa2.substitutions")
dbLoadTemplate("db/sdb0.substitutions")
dbLoadTemplate("db/sdb1.substitutions")
dbLoadTemplate("db/sdb2.substitutions")
dbLoadTemplate("db/sdb3.substitutions")
dbLoadTemplate("db/sfb0.substitutions")
dbLoadTemplate("db/sfb1.substitutions")
dbLoadTemplate("db/sfb2.substitutions")
dbLoadTemplate("db/sdp0.substitutions")
dbLoadTemplate("db/sdp1.substitutions")
dbLoadTemplate("db/sdp2.substitutions")
dbLoadTemplate("db/sdp3.substitutions")
dbLoadTemplate("db/sfp0.substitutions")
dbLoadTemplate("db/sfp1.substitutions")
dbLoadTemplate("db/sfp2.substitutions")
dbLoadTemplate("db/kickers.substitutions")

cd ${TOP}/iocBoot/${IOC}
iocInit

## Start any sequence programs
seq ps_sp_init
