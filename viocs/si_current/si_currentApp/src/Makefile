TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = si_current
# si_current.dbd will be created and installed
DBD += si_current.dbd

# si_current.dbd will be made up from these files:
si_current_DBD += base.dbd

# Include dbd files from all support applications:
#si_current_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#si_current_LIBS += xxx

# si_current_registerRecordDeviceDriver.cpp derives from si_current.dbd
si_current_SRCS += si_current_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
si_current_SRCS_DEFAULT += si_currentMain.cpp
si_current_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#si_current_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
si_current_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

