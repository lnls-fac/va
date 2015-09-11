TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

USR_CXXFLAGS_DEFAULT += -fno-operator-names
USR_CXXFLAGS_DEFAULT += -pedantic

#=============================
# Build the IOC support library

LIBRARY_IOC += bo_currentSupport

bo_currentSupport_SRCS += add_noise.cpp

bo_currentSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = bo_current
# bo_current.dbd will be created and installed
DBD += bo_current.dbd

# bo_current.dbd will be made up from these files:
bo_current_DBD += base.dbd
bo_current_DBD += add_noise.dbd

# Include dbd files from all support applications:
#bo_current_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#bo_current_LIBS += xxx

# bo_current_registerRecordDeviceDriver.cpp derives from bo_current.dbd
bo_current_SRCS += bo_current_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
bo_current_SRCS_DEFAULT += bo_currentMain.cpp
bo_current_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#bo_current_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
bo_current_LIBS += bo_currentSupport

# Finally link to the EPICS Base libraries
bo_current_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
