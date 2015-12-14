#!../../bin/linux-x86_64/injection

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/injection.dbd"
injection_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords "db/injection.db"

cd ${TOP}/iocBoot/${IOC}
iocInit
