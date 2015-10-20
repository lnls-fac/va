#!../../bin/linux-x86_64/bo_ps

## You may have to change bo_ps to something else
## everywhere it appears in this file

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/bo_ps.dbd"
bo_ps_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords("db/common.db")
dbLoadRecords("db/bend.db")
dbLoadTemplate("db/family.substitutions")
dbLoadTemplate("db/ch.substitutions")
dbLoadTemplate("db/cv.substitutions")

cd ${TOP}/iocBoot/${IOC}
iocInit

## Start any sequence programs
seq ps_sp_init
