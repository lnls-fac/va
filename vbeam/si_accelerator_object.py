# we have to decide what would go in here and what would go into database tables

import sirius.SI_V07 as _sirius
import pyaccel as _pyaccel
import numpy as _np
import si_excitation_curves as _excs

class Family(object):
    pass

_the_ring = _sirius.create_accelerator()

b1 = Family()
b1.fam_name = 'b1'
b1.pyaccel_indices = None
b1.hw_units  = 'ampere'
b1.ph_units  = 'GeV'
b1.hw_2_ph   = _excs.dipoles_b1
b1.ph_2_hw   = (0,0.1)
b1.hw_limits = (-10,10)

b2 = Family()
b2.fam_name = 'b2'
b2.pyaccel_indices = None #_np.reshape(_pyaccel.lattice.findcells(_the_ring, 'fam_name', 'b2'), (3,-1))
b2.hw_units = 'ampere'
b2.ph_units = 'GeV'
b2.hw_2_ph  = (0,10)
b2.ph_2_hw  = (0,0.1)
b2.hw_limits = (-10,10)

bpmx = Family()
bpmx.fam_name = 'bpmx'
bpmx.pyaccel_indices = None #_np.reshape(_pyaccel.lattice.findcells(_the_ring, 'fam_name', 'bpm'), (3,-1))
bpmx.hw_units = 'mm'
bpmx.ph_units = 'm'
bpmx.hw_2_ph  = (0,0.001)
bpmx.ph_2_hw  = (0,1000)

bpmy = Family()
bpmy.fam_name = 'bpmy'
bpmy.pyaccel_indices = None #_np.reshape(_pyaccel.lattice.findcells(_the_ring, 'fam_name', 'bpm'), (3,-1))
bpmy.hw_units = 'mm'
bpmy.ph_units = 'm'
bpmy.hw_2_ph  = (0,0.001)
bpmy.ph_2_hw  = (0,1000)

familis = (b1, b2, bpmx, bpmy)
