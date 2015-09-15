#!../../bin/linux-x86_64/si_beamsize

## You may have to change si_beamsize to something else
## everywhere it appears in this file

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/si_beamsize.dbd"
si_beamsize_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords "db/beamsize.db"

cd ${TOP}/iocBoot/${IOC}
iocInit

## Start any sequence programs
#seq sncxxx,"user=afonsoHost"
