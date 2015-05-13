#!../../bin/linux-x86_64/si_tune

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/si_tune.dbd"
si_tune_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords "db/tune.db"

cd ${TOP}/iocBoot/${IOC}
iocInit
