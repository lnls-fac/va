TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

USR_CXXFLAGS_DEFAULT += -fno-operator-names
USR_CXXFLAGS_DEFAULT += -pedantic

#=============================
# Build the IOC support library

LIBRARY_IOC += tb_bpmsSupport

tb_bpmsSupport_SRCS += add_noise.cpp

tb_bpmsSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================
# Build the IOC application

PROD_IOC = tb_bpms
# tb_bpms.dbd will be created and installed
DBD += tb_bpms.dbd

# tb_bpms.dbd will be made up from these files:
tb_bpms_DBD += base.dbd
tb_bpms_DBD += add_noise.dbd

# Include dbd files from all support applications:
#tb_bpms_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#tb_bpms_LIBS += xxx

# tb_bpms_registerRecordDeviceDriver.cpp derives from tb_bpms.dbd
tb_bpms_SRCS += tb_bpms_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
tb_bpms_SRCS_DEFAULT += tb_bpmsMain.cpp
tb_bpms_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#tb_bpms_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
tb_bpms_LIBS += tb_bpmsSupport

# Finally link to the EPICS Base libraries
tb_bpms_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
