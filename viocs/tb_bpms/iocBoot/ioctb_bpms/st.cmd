#!../../bin/linux-x86_64/tb_bpms

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/tb_bpms.dbd"
tb_bpms_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadTemplate("db/bpm.substitutions")

cd ${TOP}/iocBoot/${IOC}
iocInit
