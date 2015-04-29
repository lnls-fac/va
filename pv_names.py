#!/usr/bin/env python3

import sirius

fam=sirius.SI_V07.family_data
ind_bpm=fam['bpm']['index']
ind_chs=fam['chs']['index']
ind_cvs=fam['cvs']['index']

kingdom = 'SI'
subsystem=['DI','PS']
element=['-BPM-','-CHS-','-CVS-']

prefix_bpm=subsystem[0]+element[0]
prefix_chs=subsystem[1]+element[1]
prefix_cvs=subsystem[1]+element[2]
position_bpm=['M2','C1-A','C1-B','C2-A','C2-B','C4','C5-A','C5-B','M1']
position_chs=['M2','C1-A','C1-B','C2','C4','C5-A','C5-B','M1']
position_cvs=['M2','C1','C2','C4','C5','M1']

bpm={}
i=0
for j in range(20):
    sector='%02d'%(j+1)
    for e in position_bpm:
        if e == 'M1':
            if j==19:
                bpm[prefix_bpm+'01'+e]=ind_bpm[i]
            else:
                bpm[prefix_bpm+'%02d'%(j+2)+e]=ind_bpm[i]
        else:
            bpm[prefix_bpm+sector+e]=ind_bpm[i]
        i+=1
chs={}
i=0
for j in range(20):
    sector='%02d'%(j+1)
    for e in position_chs:
        if e == 'M1':
            if j==19:
                chs[prefix_chs+'01'+e]=ind_chs[i]
            else:
                chs[prefix_chs+'%02d'%(j+2)+e]=ind_chs[i]
        else:
            chs[prefix_chs+sector+e]=ind_chs[i]
        i+=1
cvs={}
i=0
for j in range(20):
    sector='%02d'%(j+1)
    for e in position_cvs:
        if e == 'M1':
            if j==19:
                cvs[prefix_cvs+'01'+e]=ind_cvs[i]
            else:
                cvs[prefix_cvs+'%02d'%(j+2)+e]=ind_cvs[i]
        else:
            cvs[prefix_cvs+sector+e]=ind_cvs[i]
        i+=1
cs={}
cs.update(chs)
cs.update(cvs)
