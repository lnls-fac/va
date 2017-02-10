#!/usr/bin/env python3

import sirius

accelerator = sirius.si.create_accelerator()

selected_families = (
    'CH',
    'CV',
    'FCH',
    'FCV',
    'QS',
    'QDA',
    'QFA',
    'QDB1',
    'QDB2',
    'QFB',
    'QDB1',
    'QDB2',
    'QFB',
    'Q1',
    'Q2',
    'Q3',
    'Q4',
    'SFA0',
    'SFA1',
    'SFA2',
    'SDA0',
    'SDA1',
    'SDA2',
    'SDA3',
    'SFB0',
    'SFB1',
    'SFB2',
    'SDB0',
    'SDB1',
    'SDB2',
    'SDB3',
    'SFP0',
    'SFP1',
    'SFP2',
    'SDP0',
    'SDP1',
    'SDP2',
    'SDP3',
)


record_names = list(sirius.si.get_device_names('SI','ps').keys())
record_names.sort()

record_names_parts = []
families = dict()
for rn in record_names:
    s = rn.split('-')[1:]
    record_names_parts.append(s)
    f = s[0]
    if f not in families:
        families[f] = []

    p = '-'.join(s[1:])
    families[f].append(p)

for family in selected_families:
    with open(family.lower()+'.substitutions', 'w') as f:
        f.write('\n')
        f.write('file "db/individual.db" {\n')
        f.write('    pattern { family, pos, num }\n')
        for pos in families[family]:
            t = '        { "' + family + '", "' + pos + '" }\n'
            if '"FAM"' in t:
                continue
            f.write(t)
            f.write('}')
