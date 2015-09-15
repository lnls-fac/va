TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = si_beamsize
# si_beamsize.dbd will be created and installed
DBD += si_beamsize.dbd

# si_beamsize.dbd will be made up from these files:
si_beamsize_DBD += base.dbd

# Include dbd files from all support applications:
#si_beamsize_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#si_beamsize_LIBS += xxx

# si_beamsize_registerRecordDeviceDriver.cpp derives from si_beamsize.dbd
si_beamsize_SRCS += si_beamsize_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
si_beamsize_SRCS_DEFAULT += si_beamsizeMain.cpp
si_beamsize_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#si_beamsize_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
si_beamsize_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

