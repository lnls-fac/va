#!../../bin/linux-x86_64/bo_current

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/bo_current.dbd"
bo_current_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords("db/current.db")

cd ${TOP}/iocBoot/${IOC}
iocInit
