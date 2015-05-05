#!../../bin/linux-x86_64/si_current

## You may have to change si_current to something else
## everywhere it appears in this file

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/si_current.dbd"
si_current_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords("db/current.db")

cd ${TOP}/iocBoot/${IOC}
iocInit

## Start any sequence programs
#seq sncxxx,"user=afonsoHost"
