TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC support library

LIBRARY_IOC += si_psSupport

si_psSupport_SRCS += ps_conversion.c

si_psSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = si_ps
# si_ps.dbd will be created and installed
DBD += si_ps.dbd

# si_ps.dbd will be made up from these files:
si_ps_DBD += base.dbd
si_ps_DBD += ps_conversion.dbd

# Include dbd files from all support applications:
#si_ps_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#si_ps_LIBS += xxx

# si_ps_registerRecordDeviceDriver.cpp derives from si_ps.dbd
si_ps_SRCS += si_ps_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
si_ps_SRCS_DEFAULT += si_psMain.cpp
si_ps_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#si_ps_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
si_ps_LIBS += si_psSupport

# Finally link to the EPICS Base libraries
si_ps_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
