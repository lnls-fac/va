#!../../bin/linux-x86_64/si_bpms

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/si_bpms.dbd"
si_bpms_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadTemplate("db/bpm.substitutions")

cd ${TOP}/iocBoot/${IOC}
iocInit
