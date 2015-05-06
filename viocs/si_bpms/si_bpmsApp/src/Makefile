TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = si_bpms
# si_bpms.dbd will be created and installed
DBD += si_bpms.dbd

# si_bpms.dbd will be made up from these files:
si_bpms_DBD += base.dbd

# Include dbd files from all support applications:
#si_bpms_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#si_bpms_LIBS += xxx

# si_bpms_registerRecordDeviceDriver.cpp derives from si_bpms.dbd
si_bpms_SRCS += si_bpms_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
si_bpms_SRCS_DEFAULT += si_bpmsMain.cpp
si_bpms_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#si_bpms_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
si_bpms_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

