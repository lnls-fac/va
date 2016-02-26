#!/usr/bin/env python3

import os
import epics
import lnls


if len(sys.argv) > 1:
    timestamp = sys.argv[1]
else:
    timestamp = None

_folder = os.path.join(lnls.folder_db, 'machine_configuration')

def read_configuration_file(machine, timestamp):
    if timestamp is not None:
        filename = machine.upper() + '_' + timestamp
    else:
        filename = machine.upper() + '_DEFAULT'

    fname = os.path.join(_folder, filename + '.txt')
    _dict = {}
    try:
        with open(fname) as f:
            for line in f:
                if not line.startswith('#') and not line.isspace():
                    line = line.replace('\n', '')
                    line = line.replace(' ', '')
                    l = line.split(':')
                    _dict[l[0]] = l[1]
    except:
        print('could not open file "' + fname + '"')
    return _dict

def set_state(machine, timestamp):
    _dict = read_configuration_file(machine, timestamp)
    for pv_name, pv_value in _dict.items():
        try:
            pv = epics.pv.PV(pv_name)
            prev_value = str(pv.get())
            if prev_value != pv_value: pv.put(pv_value)
            pv.disconnect()
        except:
            print(pv_name, ' NOT FOUND')

print('LI state'); set_state('li', timestamp); print()
print('TB state'); set_state('tb', timestamp); print()
print('BO state'); set_state('bo', timestamp); print()
print('TS state'); set_state('ts', timestamp); print()
print('SI state'); set_state('si', timestamp); print()
