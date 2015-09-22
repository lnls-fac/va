TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC support library

LIBRARY_IOC += si_rfSupport

si_rfSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = si_rf
# si_rf.dbd will be created and installed
DBD += si_rf.dbd

# si_rf.dbd will be made up from these files:
si_rf_DBD += base.dbd

# Include dbd files from all support applications:
#si_rf_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#si_rf_LIBS += xxx

# si_rf_registerRecordDeviceDriver.cpp derives from si_rf.dbd
si_rf_SRCS += si_rf_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
si_rf_SRCS_DEFAULT += si_rfMain.cpp
si_rf_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#si_rf_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
si_rf_LIBS += si_rfSupport

ifneq ($(SNCSEQ),)
    # Build sncExample into testiocSupport
    si_rf_init_SNCFLAGS += +r
	si_rf_DBD += rf_sp_init.dbd
	si_rfSupport_SRCS += rf_sp_init.stt
	si_rfSupport_LIBS += seq pv
	si_rf_LIBS += seq pv

    # Build sncProgram as a standalone program
    PROD_HOST += sncProgram
    sncProgram_SNCFLAGS += +m
    sncProgram_SRCS += sncProgram.st
    sncProgram_LIBS += seq pv
    sncProgram_LIBS += $(EPICS_BASE_HOST_LIBS)
endif

# Finally link to the EPICS Base libraries
si_rf_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
