#!/usr/bin/env python3

import model


record_names = model.sirius.bo.record_names.get_record_names()

bpms = []
power_supplies_sp = []
power_supplies_rb = []
parameters = []

for record_name in record_names.keys():
    if 'BPM-' in record_name:
        bpms.append(record_name)
    elif 'PS-' in record_name:
        power_supplies_sp.append(record_name + '-SP')
        power_supplies_rb.append(record_name + '-RB')
    elif 'PA-' in record_name:
        parameters.append(record_name)
    else:
        print('Parameter', record_name, 'not found!')

read_only_pvs = bpms + parameters + power_supplies_rb
read_write_pvs = power_supplies_sp

database = {}
for bpm in bpms:
    database[bpm] = {'type' : 'float', 'count': 2}
for parameter in parameters:
    database[parameter] = {'type' : 'float', 'count': 1, 'value': 0.0}
for ps in power_supplies_sp:
    database[ps] = {'type' : 'float', 'count': 1, 'value': 0.0}
for ps in power_supplies_rb:
    database[ps] = {'type' : 'float', 'count': 1, 'value': 0.0}
