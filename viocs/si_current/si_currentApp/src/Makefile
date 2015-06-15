TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

USR_CXXFLAGS_DEFAULT += -fno-operator-names
USR_CXXFLAGS_DEFAULT += -pedantic

#=============================
# Build the IOC support library

LIBRARY_IOC += si_currentSupport

si_currentSupport_SRCS += add_noise.cpp

si_currentSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = si_current
# si_current.dbd will be created and installed
DBD += si_current.dbd

# si_current.dbd will be made up from these files:
si_current_DBD += base.dbd
si_current_DBD += add_noise.dbd

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

# Link in the code from the support library
si_current_LIBS += si_currentSupport

# Finally link to the EPICS Base libraries
si_current_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
