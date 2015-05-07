#!../../bin/linux-x86_64/si_ps

## You may have to change si_ps to something else
## everywhere it appears in this file

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/si_ps.dbd"
si_ps_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadTemplate("db/cs.substitutions")

cd ${TOP}/iocBoot/${IOC}
iocInit

## Start any sequence programs
#seq sncxxx,"user=afonsoHost"
