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
dbLoadTemplate("db/qda.substitutions")
dbLoadTemplate("db/qdb1.substitutions")
dbLoadTemplate("db/qdb2.substitutions")
dbLoadTemplate("db/qfa.substitutions")
dbLoadTemplate("db/qfb.substitutions")
dbLoadTemplate("db/qf1.substitutions")
dbLoadTemplate("db/qf2.substitutions")
dbLoadTemplate("db/qf3.substitutions")
dbLoadTemplate("db/qf4.substitutions")
dbLoadTemplate("db/qs.substitutions")
dbLoadTemplate("db/sd1j.substitutions")
dbLoadTemplate("db/sd2j.substitutions")
dbLoadTemplate("db/sd3j.substitutions")
dbLoadTemplate("db/sd1k.substitutions")
dbLoadTemplate("db/sd2k.substitutions")
dbLoadTemplate("db/sd3k.substitutions")
dbLoadTemplate("db/sda.substitutions")
dbLoadTemplate("db/sdb.substitutions")
dbLoadTemplate("db/sf1j.substitutions")
dbLoadTemplate("db/sf2j.substitutions")
dbLoadTemplate("db/sf1k.substitutions")
dbLoadTemplate("db/sf2k.substitutions")
dbLoadTemplate("db/sfa.substitutions")
dbLoadTemplate("db/sfb.substitutions")

cd ${TOP}/iocBoot/${IOC}
iocInit

## Start any sequence programs
seq ps_sp_init
