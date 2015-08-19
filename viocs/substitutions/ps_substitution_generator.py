#!/usr/bin/env python3

import sirius


selected_families = (
    'CHF',
    'CHS',
    'CVF',
    'CVS',
    'QDA',
    'QDB1',
    'QDB2',
    'QF1',
    'QF2',
    'QF3',
    'QF4',
    'QFA',
    'QFB',
    'QS',
    'SD1',
    'SD2',
    'SD3',
    'SD4',
    'SD5',
    'SD6',
    'SDA',
    'SDB',
    'SF1',
    'SF2',
    'SF3',
    'SF4',
    'SFA',
    'SFB',
)


record_names_dict = sirius.si.record_names.get_record_names()
record_names = list(record_names_dict.keys())
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

    f = open(family.lower()+'.substitutions', 'w')
    f.write('\n')
    f.write('file "db/individual.db" {\n')
    f.write('    pattern { family, pos }\n')
    for pos in families[family]:
        t = '        { "' + family + '", "' + pos + '" }\n'
        if '"FAM"' in t:
            continue
        f.write(t)
    f.write('}')
    f.close()