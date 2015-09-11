#!../../bin/linux-x86_64/bo_bpms

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/bo_bpms.dbd"
bo_bpms_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadTemplate("db/bpm.substitutions")

cd ${TOP}/iocBoot/${IOC}
iocInit
