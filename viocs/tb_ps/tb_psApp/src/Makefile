TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

USR_CXXFLAGS_DEFAULT += -fno-operator-names
USR_CXXFLAGS_DEFAULT += -pedantic

#=============================
# Build the IOC support library

LIBRARY_IOC += tb_psSupport

tb_psSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = tb_ps
# tb_ps.dbd will be created and installed
DBD += tb_ps.dbd

# tb_ps.dbd will be made up from these files:
tb_ps_DBD += base.dbd

# Include dbd files from all support applications:
#tb_ps_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#tb_ps_LIBS += xxx

# tb_ps_registerRecordDeviceDriver.cpp derives from tb_ps.dbd
tb_ps_SRCS += tb_ps_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
tb_ps_SRCS_DEFAULT += tb_psMain.cpp
tb_ps_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#tb_ps_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
tb_ps_LIBS += tb_psSupport

ifneq ($(SNCSEQ),)
    # Build sncExample into testiocSupport
    tb_ps_init_SNCFLAGS += +r
	tb_ps_DBD += ps_sp_init.dbd
	tb_psSupport_SRCS += ps_sp_init.stt
	tb_psSupport_LIBS += seq pv
	tb_ps_LIBS += seq pv

    # Build sncProgram as a standalone program
    PROD_HOST += sncProgram
    sncProgram_SNCFLAGS += +m
    sncProgram_SRCS += sncProgram.st
    sncProgram_LIBS += seq pv
    sncProgram_LIBS += $(EPICS_BASE_HOST_LIBS)
endif

# Finally link to the EPICS Base libraries
tb_ps_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
