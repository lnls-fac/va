#!/usr/bin/env python3

import model


record_names = model.sirius.si.record_names.get_record_names()

sidi_bpms = []
sips = []
sipa = []
sidi = []

for record_name in record_names.keys():
    if 'BPM-' in record_name:
        sidi_bpms.append(record_name)
    elif 'DI-' in record_name:
        sidi.append(record_name)
    elif 'PS-' in record_name:
        sips.append(record_name)
    elif 'PA-' in record_name:
        sipa.append(record_name)
    else:
        print('Parameter', record_name, 'not found!')

read_only_pvs = sidi_bpms + sipa + sidi
read_write_pvs = sips

database = {}
for p in sidi_bpms:
    database[p] = {'type' : 'float', 'count': 2}
for p in sidi:
    database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
for p in sips:
    database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
for p in sipa:
    database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
