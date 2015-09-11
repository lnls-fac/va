TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

USR_CXXFLAGS_DEFAULT += -fno-operator-names
USR_CXXFLAGS_DEFAULT += -pedantic

#=============================
# Build the IOC support library

LIBRARY_IOC += bo_psSupport

bo_psSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = bo_ps
# bo_ps.dbd will be created and installed
DBD += bo_ps.dbd

# bo_ps.dbd will be made up from these files:
bo_ps_DBD += base.dbd

# Include dbd files from all support applications:
#bo_ps_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#bo_ps_LIBS += xxx

# bo_ps_registerRecordDeviceDriver.cpp derives from bo_ps.dbd
bo_ps_SRCS += bo_ps_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
bo_ps_SRCS_DEFAULT += bo_psMain.cpp
bo_ps_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#bo_ps_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
bo_ps_LIBS += bo_psSupport

ifneq ($(SNCSEQ),)
    # Build sncExample into testiocSupport
    bo_ps_init_SNCFLAGS += +r
	bo_ps_DBD += ps_sp_init.dbd
	bo_psSupport_SRCS += ps_sp_init.stt
	bo_psSupport_LIBS += seq pv
	bo_ps_LIBS += seq pv

    # Build sncProgram as a standalone program
    PROD_HOST += sncProgram
    sncProgram_SNCFLAGS += +m
    sncProgram_SRCS += sncProgram.st
    sncProgram_LIBS += seq pv
    sncProgram_LIBS += $(EPICS_BASE_HOST_LIBS)
endif

# Finally link to the EPICS Base libraries
bo_ps_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
