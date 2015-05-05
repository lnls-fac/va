#!/usr/bin/env python3

import model


record_names = model.sirius.si.record_names.get_record_names()

bpms = []
power_supplies_sp = []
power_supplies_rb = []
sipa = []
sidi = []

for record_name in record_names.keys():
    if 'BPM-' in record_name:
        bpms.append(record_name)
    elif 'PS-' in record_name:
        power_supplies_sp.append(record_name + '-SP')
        power_supplies_rb.append(record_name + '-RB')
    elif 'PA-' in record_name:
        sipa.append(record_name)
    elif 'DI-' in record_name:
        sidi.append(record_name)
    else:
        print('Parameter', record_name, 'not found!')

read_only_pvs = bpms + sidi + sipa + power_supplies_rb
read_write_pvs = power_supplies_sp

database = {}
for parameter in bpms:
    database[parameter] = {'type' : 'float', 'count': 2}
for parameter in sidi:
    database[parameter] = {'type' : 'float', 'count': 1, 'value': 0.0}
for parameter in sipa:
    database[parameter] = {'type' : 'float', 'count': 1, 'value': 0.0}
for parameter in power_supplies_sp:
    database[parameter] = {'type' : 'float', 'count': 1, 'value': 0.0}
for parameter in power_supplies_rb:
    database[parameter] = {'type' : 'float', 'count': 1, 'value': 0.0}
