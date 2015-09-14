TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

USR_CXXFLAGS_DEFAULT += -fno-operator-names
USR_CXXFLAGS_DEFAULT += -pedantic

#=============================
# Build the IOC support library

LIBRARY_IOC += ts_bpmsSupport

ts_bpmsSupport_SRCS += add_noise.cpp

ts_bpmsSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = ts_bpms
# ts_bpms.dbd will be created and installed
DBD += ts_bpms.dbd

# ts_bpms.dbd will be made up from these files:
ts_bpms_DBD += base.dbd
ts_bpms_DBD += add_noise.dbd

# Include dbd files from all support applications:
#ts_bpms_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#ts_bpms_LIBS += xxx

# ts_bpms_registerRecordDeviceDriver.cpp derives from ts_bpms.dbd
ts_bpms_SRCS += ts_bpms_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
ts_bpms_SRCS_DEFAULT += ts_bpmsMain.cpp
ts_bpms_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#ts_bpms_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
ts_bpms_LIBS += ts_bpmsSupport

# Finally link to the EPICS Base libraries
ts_bpms_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
