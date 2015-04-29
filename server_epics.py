#!/usr/bin/env python3

from pcaspy import Driver, SimpleServer
import numpy
import sirius
import pyaccel
import pv_names

def orbit(accel):
    orbit=pyaccel.tracking.findorbit6(accel,'open')
    global orbitx
    orbitx=orbit[0,:]
    global orbity
    orbity=orbit[2,:]

accel=sirius.SI_V07.create_accelerator()
pyaccel.tracking.set6dtracking(accel)
orbit(accel)

bpm=pv_names.bpm
cs=pv_names.cs
pvdb = {}
for key in bpm.keys():
    pvdb[key]= {'type' : 'float', 'count': 2 }
for key in cs.keys():
    pvdb[key]= {'type': 'float', 'count': 1 }

class myDriver(Driver):
    def  __init__(self,accel):
        super(myDriver, self).__init__()
        self.accel=accel

    def read(self,reason):
        if reason in bpm.keys():
            ind = bpm[reason]
            value = [orbitx[ind],orbity[ind]]
        elif reason in cs.keys():
            ind = cs[reason]
            if 'CHS' in reason:
                value = self.accel[ind].hkick_polynom
            else:
                value = self.accel[ind].vkick_polynom
        else:
            value = self.getParam(reason)
        return value

    def write(self,reason,value):
        if reason in cs.keys():
            ind = cs[reason]
            if 'CHS' in reason:
                self.accel[ind].hkick_polynom = value
            else:
                self.accel[ind].vkick_polynom = value
            orbit(self.accel)

if __name__ == '__main__':
    server = SimpleServer()
    server.createPV(pv_names.kingdom,pvdb)
    driver = myDriver(accel)

    while True:
        server.process(0.1)
