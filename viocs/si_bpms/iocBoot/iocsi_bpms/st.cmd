#!../../bin/linux-x86_64/si_bpms

## You may have to change si_bpms to something else
## everywhere it appears in this file

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/si_bpms.dbd"
si_bpms_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadTemplate("db/bpm.substitutions")

cd ${TOP}/iocBoot/${IOC}
iocInit

## Start any sequence programs
#seq sncxxx,"user=afonsoHost"
