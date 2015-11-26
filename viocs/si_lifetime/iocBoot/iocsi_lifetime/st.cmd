#!../../bin/linux-x86_64/si_lifetime

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/si_lifetime.dbd"
si_lifetime_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords "db/lifetime.db"


cd ${TOP}/iocBoot/${IOC}
iocInit

seq calcLifeTime
