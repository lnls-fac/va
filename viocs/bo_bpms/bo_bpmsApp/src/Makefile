TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

USR_CXXFLAGS_DEFAULT += -fno-operator-names
USR_CXXFLAGS_DEFAULT += -pedantic

#=============================
# Build the IOC support library

LIBRARY_IOC += bo_bpmsSupport

bo_bpmsSupport_SRCS += add_noise.cpp

bo_bpmsSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = bo_bpms
# bo_bpms.dbd will be created and installed
DBD += bo_bpms.dbd

# bo_bpms.dbd will be made up from these files:
bo_bpms_DBD += base.dbd
bo_bpms_DBD += add_noise.dbd

# Include dbd files from all support applications:
#bo_bpms_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#bo_bpms_LIBS += xxx

# bo_bpms_registerRecordDeviceDriver.cpp derives from bo_bpms.dbd
bo_bpms_SRCS += bo_bpms_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
bo_bpms_SRCS_DEFAULT += bo_bpmsMain.cpp
bo_bpms_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#bo_bpms_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
bo_bpms_LIBS += bo_bpmsSupport

# Finally link to the EPICS Base libraries
bo_bpms_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
