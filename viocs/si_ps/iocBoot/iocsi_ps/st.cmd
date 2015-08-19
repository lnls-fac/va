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
dbLoadTemplate("db/chs.substitutions")
dbLoadTemplate("db/cvs.substitutions")
dbLoadTemplate("db/qda.substitutions")
dbLoadTemplate("db/qdb1.substitutions")
dbLoadTemplate("db/qdb2.substitutions")
dbLoadTemplate("db/qf1.substitutions")
dbLoadTemplate("db/qf2.substitutions")
dbLoadTemplate("db/qf3.substitutions")
dbLoadTemplate("db/qf4.substitutions")
dbLoadTemplate("db/qfa.substitutions")
dbLoadTemplate("db/qfb.substitutions")
dbLoadTemplate("db/qs.substitutions")
dbLoadTemplate("db/sd1.substitutions")
dbLoadTemplate("db/sd2.substitutions")
dbLoadTemplate("db/sd3.substitutions")
dbLoadTemplate("db/sd4.substitutions")
dbLoadTemplate("db/sd5.substitutions")
dbLoadTemplate("db/sd6.substitutions")
dbLoadTemplate("db/sda.substitutions")
dbLoadTemplate("db/sdb.substitutions")
dbLoadTemplate("db/sf1.substitutions")
dbLoadTemplate("db/sf2.substitutions")
dbLoadTemplate("db/sf3.substitutions")
dbLoadTemplate("db/sf4.substitutions")
dbLoadTemplate("db/sfa.substitutions")
dbLoadTemplate("db/sfb.substitutions")

cd ${TOP}/iocBoot/${IOC}
iocInit

## Start any sequence programs
seq ps_sp_init
