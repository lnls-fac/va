#!/usr/bin/env python3

import model


record_names = model.sirius.bo.record_names.get_record_names()

bodi_bpms = []
bops = []
bopa = []
bodi = []

for record_name in record_names.keys():
    if 'BPM-' in record_name:
        bodi_bpms.append(record_name)
    elif 'DI-' in record_name:
        bodi.append(record_name)
    elif 'PS-' in record_name:
        bops.append(record_name)
    elif 'PA-' in record_name:
        bopa.append(record_name)
    else:
        print('Parameter', record_name, 'not found!')

read_only_pvs = bodi_bpms + bopa + bodi
read_write_pvs = bops

database = {}
for p in bodi_bpms:
    database[p] = {'type' : 'float', 'count': 2}
for p in bodi:
    database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
for p in bops:
    database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
for p in bopa:
    database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
