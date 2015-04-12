#!/usr/bin/env python3

import xmlrpclib

import vabeam_si as _si
import vabeam_bo as _bo


class VABeam:

    def __init__(self):

        self.clock = None  # global clock for the system
        self.si    = _si.VAccelerator(self.clock)
        self.bo    = _bo.VAccelerator(self.clock)

    def read_pv(self, pv):
        if 'SI' in pv:
            self.si.read_pv(pv)
        elif 'BO' in pv:
            self.bo.read_pv(pv)

    def write_pv(self, pv, value):
        if 'SI' in pv:
            self.si.write_pv(pv, value)
        elif 'BO' in pv:
            self.bo.write_pv(pv, value)
