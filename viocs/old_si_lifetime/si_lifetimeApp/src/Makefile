TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE

#=============================
# Build the IOC support library

LIBRARY_IOC += si_lifetimeSupport

# xxxRecord.h will be created from xxxRecord.dbd
DBDINC += xxxRecord
# Install devXxxSoft.dbd into <top>/dbd
DBD += xxxSupport.dbd

# Compile and add the code to the support library
si_lifetimeSupport_SRCS += xxxRecord.c
si_lifetimeSupport_SRCS += devXxxSoft.c


si_lifetimeSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = si_lifetime
# si_lifetime.dbd will be created and installed
DBD += si_lifetime.dbd

# si_lifetime.dbd will be made up from these files:
si_lifetime_DBD += base.dbd
si_lifetime_DBD += xxxSupport.dbd

# si_lifetime_registerRecordDeviceDriver.cpp derives from si_lifetime.dbd
si_lifetime_SRCS += si_lifetime_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
si_lifetime_SRCS_DEFAULT += si_lifetimeMain.cpp
si_lifetime_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#si_lifetime_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
si_lifetime_LIBS += si_lifetimeSupport

# NOTE: To build SNL programs, SNCSEQ must be defined
# in the <top>/configure/RELEASE file

ifneq ($(SNCSEQ),)
    # Build calcLifeTime into si_lifetimeSupport
    calcLifeTime_SNCFLAGS += +r
    si_lifetime_DBD += calcLifeTime.dbd
    si_lifetimeSupport_SRCS += calcLifeTime.stt
    si_lifetimeSupport_LIBS += seq pv
    si_lifetime_LIBS += seq pv

    # Build sncProgram as a standalone program
    PROD_HOST += sncProgram
    sncProgram_SNCFLAGS += +m
    sncProgram_SRCS += sncProgram.st
    sncProgram_LIBS += seq pv
    sncProgram_LIBS += $(EPICS_BASE_HOST_LIBS)
endif

# Finally link to the EPICS Base libraries
si_lifetime_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
