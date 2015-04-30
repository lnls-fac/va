#!/usr/bin/env python3

import sirius as _sirius

kingdom = 'SI'
subsystem = ['DI','PS','PA']
element = ['-BPM-','-CHS-','-CVS-']

fam=_sirius.SI_V07.family_data

# --- BPMS ---
ind_bpm=fam['bpm']['index']
prefix_bpm=subsystem[0]+element[0]
position_bpm=['M2','C1-A','C1-B','C2-A','C2-B','C4','C5-A','C5-B','M1']
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

# --- CHS ---
ind_chs=fam['chs']['index']
prefix_chs=subsystem[1]+element[1]
position_chs=['M2','C1-A','C1-B','C2','C4','C5-A','C5-B','M1']
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

# --- CVS ---
ind_cvs=fam['cvs']['index']
prefix_cvs=subsystem[1]+element[2]
position_cvs=['M2','C1','C2','C4','C5','M1']
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

# --- CS ---
cs={}
cs.update(chs)
cs.update(cvs)

# --- PARAMETERS ---
pvnames = (
    'SIPA-TUNEH',   'SIPA-TUNEV',  'SIPA-TUNES',
    'SIPA-CHROMX',  'SIPA-CHROMY',
    'SIPA-TVHOUR',  'SIPA-TVMIN',
    'SIPA-SIGX',    'SIPA-SIGY',   'SIPA-SIGS',
    'SIPA-EMITX',   'SIPA-EMITY',
    'SIPA-SIGX',    'SIPA-SIGY',   'SIPA-SIGS',
    'SIPA-CURRENT', 'SIPA-CURRENT'
    )
parameters = {}
for i in range(len(pvnames)):
    parameters[pvnames[i]] = i




### EPICS PV DATABASE ###

database = {}

# - bpms -
for key in bpm.keys():
    database['SI'+key] = {'type' : 'float', 'count': 2}

# - parameters -
for key in parameters.keys():
    database[key] = {'type':'float', 'count':1}