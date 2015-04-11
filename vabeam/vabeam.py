#!/usr/bin/env python3

import xmlrpclib

import vabeam_si as _si
import vabeam_bo as _bo


class VABeam:

    def __init__(self):

        self.clock = clock  # global clock for the system
        self.si    = _si.VAccelerator(self.clock)
        self.bo    = _bo.VAccelerator(self.clock)

    def read_pv(self, pv):
        pass

    def write_pv(self, pv, value):
        pass
