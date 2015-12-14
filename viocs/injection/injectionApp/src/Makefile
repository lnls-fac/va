TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = injection
# injection.dbd will be created and installed
DBD += injection.dbd

# injection.dbd will be made up from these files:
injection_DBD += base.dbd

# Include dbd files from all support applications:
#injection_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#injection_LIBS += xxx

# injection_registerRecordDeviceDriver.cpp derives from injection.dbd
injection_SRCS += injection_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
injection_SRCS_DEFAULT += injectionMain.cpp
injection_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#injection_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
injection_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
