#!../../bin/linux-x86_64/si_current

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/si_current.dbd"
si_current_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords("db/current.db")

cd ${TOP}/iocBoot/${IOC}
iocInit
