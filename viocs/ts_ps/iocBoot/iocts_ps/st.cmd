#!../../bin/linux-x86_64/ts_ps

## You may have to change ts_ps to something else
## everywhere it appears in this file

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/ts_ps.dbd"
ts_ps_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords("db/common.db")
dbLoadTemplate("db/ch.substitutions")
dbLoadTemplate("db/cv.substitutions")
dbLoadTemplate("db/quad.substitutions")
dbLoadTemplate("db/bend.substitutions")
dbLoadTemplate("db/septa.substitutions")

cd ${TOP}/iocBoot/${IOC}
iocInit

## Start any sequence programs
seq ps_sp_init
