TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC support library

LIBRARY_IOC += bo_rfSupport

bo_rfSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = bo_rf
# bo_rf.dbd will be created and installed
DBD += bo_rf.dbd

# bo_rf.dbd will be made up from these files:
bo_rf_DBD += base.dbd

# Include dbd files from all support applications:
#bo_rf_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#bo_rf_LIBS += xxx

# bo_rf_registerRecordDeviceDriver.cpp derives from bo_rf.dbd
bo_rf_SRCS += bo_rf_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
bo_rf_SRCS_DEFAULT += bo_rfMain.cpp
bo_rf_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#bo_rf_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
bo_rf_LIBS += bo_rfSupport

ifneq ($(SNCSEQ),)
    # Build sncExample into testiocSupport
    bo_rf_init_SNCFLAGS += +r
	bo_rf_DBD += rf_sp_init.dbd
	bo_rfSupport_SRCS += rf_sp_init.stt
	bo_rfSupport_LIBS += seq pv
	bo_rf_LIBS += seq pv

    # Build sncProgram as a standalone program
    PROD_HOST += sncProgram
    sncProgram_SNCFLAGS += +m
    sncProgram_SRCS += sncProgram.st
    sncProgram_LIBS += seq pv
    sncProgram_LIBS += $(EPICS_BASE_HOST_LIBS)
endif

# Finally link to the EPICS Base libraries
bo_rf_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
