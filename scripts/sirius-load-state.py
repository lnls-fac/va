#!/usr/bin/env python3

import os
import epics
import lnls


if len(sys.argv) > 2:
    machine = sys.argv[1]
    filename = sys.argv[2]
elif len(sys.argv) > 1:
    machine = sys.argv[1]
    filename = None
else:
    machine = 'all'
    filename = None

_folder = os.path.join(lnls.folder_db, 'machine_configuration')
_machines = ['li', 'tb', 'bo', 'ts', 'si']

def server_connected():
    test_pv = epics.pv.PV('VA-SIDI-CURRENT')
    if test_pv.get() is not None:
        return True
    else:
        return False

def read_configuration_file(machine, filename):
    if not filename.endswith('.txt'): filename = filename + '.txt'
    filepath = os.path.join(_folder, filename)

    _dict = {}
    try:
        with open(filepath) as f:
            for line in f:
                if not line.startswith('#') and not line.isspace():
                    line = line.replace('\n', '')
                    line = line.replace(' ', '')
                    l = line.split(':')
                    _dict[l[0]] = l[1]
    except:
        print('Could not open file "' + filename + '"')
    return _dict

def set_state(machine, timestamp):
    print('Setting %s state...'%machine.lower())
    _dict = read_configuration_file(machine, timestamp)
    for pv_name, pv_value in _dict.items():
        try:
            pv = epics.pv.PV(pv_name)
            prev_value = str(pv.get())
            if prev_value != pv_value: pv.put(pv_value)
            pv.disconnect()
        except:
            print('PV "', pv_name, '" NOT FOUND')

if server_connected():
    if machine.lower() == 'all':
        for machine in _machines:
            if filename is not None:
                fn = machine.upper() + '_' + filename
            else:
                fn = machine.upper() + '_DEFAULT.txt'
            set_state(machine.lower(), fn)
        print('Load state done!')
    elif machine.lower() in _machines:
        if filename is None:
            filename = machine.upper() + '_DEFAULT.txt'
        set_state(machine.lower(), filename)
        print('Load state done!')
    else:
        print('Machine "' + machine.upper() + '" not found.')
else:
    print('Virtual accelerator server not found.')
