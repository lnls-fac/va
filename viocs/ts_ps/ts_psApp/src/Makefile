TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

USR_CXXFLAGS_DEFAULT += -fno-operator-names
USR_CXXFLAGS_DEFAULT += -pedantic

#=============================
# Build the IOC support library

LIBRARY_IOC += ts_psSupport

ts_psSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = ts_ps
# ts_ps.dbd will be created and installed
DBD += ts_ps.dbd

# ts_ps.dbd will be made up from these files:
ts_ps_DBD += base.dbd

# Include dbd files from all support applications:
#ts_ps_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#ts_ps_LIBS += xxx

# ts_ps_registerRecordDeviceDriver.cpp derives from ts_ps.dbd
ts_ps_SRCS += ts_ps_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
ts_ps_SRCS_DEFAULT += ts_psMain.cpp
ts_ps_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#ts_ps_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
ts_ps_LIBS += ts_psSupport

ifneq ($(SNCSEQ),)
    # Build sncExample into testiocSupport
    ts_ps_init_SNCFLAGS += +r
	ts_ps_DBD += ps_sp_init.dbd
	ts_psSupport_SRCS += ps_sp_init.stt
	ts_psSupport_LIBS += seq pv
	ts_ps_LIBS += seq pv

    # Build sncProgram as a standalone program
    PROD_HOST += sncProgram
    sncProgram_SNCFLAGS += +m
    sncProgram_SRCS += sncProgram.st
    sncProgram_LIBS += seq pv
    sncProgram_LIBS += $(EPICS_BASE_HOST_LIBS)
endif

# Finally link to the EPICS Base libraries
ts_ps_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
