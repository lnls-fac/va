#!../../bin/linux-x86_64/ts_bpms

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/ts_bpms.dbd"
ts_bpms_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadTemplate("db/bpm.substitutions")

cd ${TOP}/iocBoot/${IOC}
iocInit
