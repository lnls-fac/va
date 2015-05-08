TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = si_tune
# si_tune.dbd will be created and installed
DBD += si_tune.dbd

# si_tune.dbd will be made up from these files:
si_tune_DBD += base.dbd

# Include dbd files from all support applications:
#si_tune_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#si_tune_LIBS += xxx

# si_tune_registerRecordDeviceDriver.cpp derives from si_tune.dbd
si_tune_SRCS += si_tune_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
si_tune_SRCS_DEFAULT += si_tuneMain.cpp
si_tune_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#si_tune_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
si_tune_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

