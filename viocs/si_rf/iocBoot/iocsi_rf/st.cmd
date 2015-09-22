#!../../bin/linux-x86_64/si_rf

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/si_rf.dbd"
si_rf_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords("db/rf.db")

cd ${TOP}/iocBoot/${IOC}
iocInit

## Start any sequence programs
seq rf_sp_init
