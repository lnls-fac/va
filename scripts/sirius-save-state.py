#!/usr/bin/env python3

import os
import sys
import time
import datetime
import epics
import va
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

_max_pv_name_length = 50
_folder = os.path.join(lnls.folder_db, 'machine_configuration')
_machines = ['li', 'tb', 'bo', 'ts', 'si']
_rname_functions = {
    'li':va.pvs.li.get_read_write_pvs,
    'tb':va.pvs.tb.get_read_write_pvs,
    'bo':va.pvs.bo.get_read_write_pvs,
    'ts':va.pvs.ts.get_read_write_pvs,
    'si':va.pvs.si.get_read_write_pvs,
}

def server_connected():
    test_pv = epics.pv.PV('VA-SIDI-CURRENT')
    if test_pv.get() is not None:
        return True
    else:
        return False

def get_machine_pvs(machine):
    pvs = get_vaca_pvs(machine)
    return pvs

def get_vaca_pvs(machine):
    read_write_pvs = _rname_functions[machine.lower()]()
    pvs = []
    for pv_name in read_write_pvs:
        if 'FK-' not in pv_name:
            pvs.append('VA-' + pv_name)
    return pvs

def insert_new_pv(pv_name, lines):
    try:
        pv = epics.pv.PV(pv_name)
        pv_value = pv.get()
        pv_units = str(pv.units).split("'")[1]
        text = pv_name + ' ' * (_max_pv_name_length - len(pv_name)) + ' : ' + str(pv_value) + pv_units
        pv.disconnect()
    except:
        text = pv_name + ' ' * (_max_pv_name_length - len(pv_name)) + ' # [NOT FOUND]'
    lines.append(text)

def save_state(machine, timestamp, filename=None):
    if filename is None:
        filename = machine.upper() + '_' + timestamp.strftime('%Y-%m-%d_%H-%M-%S') + '.txt'
    elif not filename.endswith('.txt'):
        filename = filename + '.txt'
    filepath = os.path.join(_folder, filename)

    if not os.path.isfile(filepath):
        print('Saving %s state...'%(machine.upper()))
        pvs = get_machine_pvs(machine)
        lines = []

        lines.append('# SIRIUS %s MACHINE CONFIGURATION'%(machine.upper()))
        lines.append('# ==================================')
        lines.append('#')

        ts = timestamp.strftime('%Y-%m-%d %H:%M:%S') + '  (by sirius-save-machine-configuration.py)'
        lines.append('# TIMESTAMP ' + ts)
        lines.append('')

        # inserts PVs
        for pv_name in pvs:
            insert_new_pv(pv_name, lines)

        try:
            f = open(filepath, "w")
            for line in lines:
                print(line, file=f)
            print('%s state saved in file "%s"\n'%(machine.upper(), filename))
        except IOError:
            print('Could not open file "' + filepath + '"')
    else:
        print('File "' + filepath + '" already exists.')

if server_connected():
    timestamp = datetime.datetime.fromtimestamp(time.time())
    if machine.lower() == 'all':
        for machine in _machines:
            fn = machine.upper() + '_' + filename if filename is not None else None
            save_state(machine.lower(), timestamp, fn)
    elif machine.lower() in _machines:
        save_state(machine.lower(), timestamp, filename)
    else:
        print('Machine "' + machine.upper() + '" not found.')
else:
    print('Virtual accelerator server not found.')
