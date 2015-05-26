TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

USR_CXXFLAGS_DEFAULT += -fno-operator-names
USR_CXXFLAGS_DEFAULT += -pedantic

#=============================
# Build the IOC support library

LIBRARY_IOC += si_bpmsSupport

si_bpmsSupport_SRCS += add_noise.cpp

si_bpmsSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = si_bpms
# si_bpms.dbd will be created and installed
DBD += si_bpms.dbd

# si_bpms.dbd will be made up from these files:
si_bpms_DBD += base.dbd
si_bpms_DBD += add_noise.dbd

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

# Link in the code from the support library
si_bpms_LIBS += si_bpmsSupport

# Finally link to the EPICS Base libraries
si_bpms_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
