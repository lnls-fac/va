#!/usr/bin/env python3

import os
import epics
import lnls

_folder = os.path.join(lnls.folder_db, 'configuration')

def read_configuration_file(machine):
    fname = os.path.join(_folder, machine.lower() + '.txt')
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

def set_state(machine):
    _dict = read_configuration_file(machine)
    for pv_name, pv_value in _dict.items():
        try:
            pv = epics.pv.PV(pv_name)
            prev_value = str(pv.get())
            if prev_value != pv_value: pv.put(pv_value)
            pv.disconnect()
        except:
            pass

print('LI state'); set_state('li'); print()
print('TB state'); set_state('tb'); print()
print('BO state'); set_state('bo'); print()
print('TS state'); set_state('ts'); print()
print('SI state'); set_state('si'); print()
