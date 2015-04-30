#!/usr/bin/env python3

import time
import math
import numpy
from epics import caget,caput
from operator import itemgetter
import pv_names

begin=time.time()

bpm=numpy.array(sorted(pv_names.bpm.items(), key=itemgetter(1)))
chs=numpy.array(sorted(pv_names.chs.items(), key=itemgetter(1)))
cvs=numpy.array(sorted(pv_names.cvs.items(), key=itemgetter(1)))

def orb_bpms(bpm):
    prefix=pv_names.kingdom
    orb=numpy.zeros((2,len(bpm)))
    i=0
    for key in bpm[:,0]:
        orb[:,i]=caget(prefix+key)
        i+=1
    x=orb[0,:]
    y=orb[1,:]
    return x,y

def matriz_resposta(dk,bpm,chs,cvs):
    M=numpy.zeros((2*len(bpm),len(chs)+len(cvs)))
    i=0
    prefix='SI'
    for key in chs[:,0]:
        k=caget(prefix+key)

        caput(prefix+key, k + dk/2.0 )
        x1,y1=orb_bpms(bpm)
        r1=numpy.concatenate((x1,y1))

        caput(prefix+key, k - dk/2.0 )
        x2,y2=orb_bpms(bpm)
        r2=numpy.concatenate((x2,y2))

        delta=r1-r2
        M[:,i]=delta/dk

        caput(prefix+key, k)
        i+=1
    for key in cvs[:,0]:
        k=caget(prefix+key)

        caput(prefix+key, k + dk/2.0 )
        x3,y3=orb_bpms(bpm)
        r3=numpy.concatenate((x3,y3))

        caput(prefix+key, k - dk/2.0 )
        x4,y4=orb_bpms(bpm)
        r4=numpy.concatenate((x4,y4))

        delta=r3-r4
        M[:,i]=delta/dk

        caput(prefix+key, k)
        i+=1
    return M

M=matriz_resposta(1e-6,bpm,chs,cvs)
#numpy.savetxt('matriz_resposta_epics.txt', M, fmt='%-14.8f')

end=time.time()
tempo=end-begin
print(tempo)
