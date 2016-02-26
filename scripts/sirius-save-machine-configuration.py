#!/usr/bin/env python3

import os
import time
import datetime
import epics
import va
import lnls


_max_pv_name_length = 50
_folder = os.path.join(lnls.folder_db, 'machine_configuration')
_rname_functions = {
    'li':va.pvs.li.get_read_write_pvs,
    'tb':va.pvs.tb.get_read_write_pvs,
    'bo':va.pvs.bo.get_read_write_pvs,
    'ts':va.pvs.ts.get_read_write_pvs,
    'si':va.pvs.si.get_read_write_pvs,
}


def get_all_defined_pvs(machine):
    record_names = _rname_functions[machine.lower()]()
    return sorted(record_names)


def insert_new_pv(pv_name, lines):
    try:
        pv = epics.pv.PV(pv_name)
        pv_value = pv.get()
        pv_units = str(pv.units).split("'")[1]
        text = pv_name + ' ' * (_max_pv_name_length - len(pv_name)) + ' : ' + str(pv_value) + pv_units
        pv.disconnect()
    except:
        text = pv_name + ' # [NOT FOUND]'
    lines.append(text)


def save_state(machine, timestamp):

    pvs = get_all_defined_pvs(machine)
    lines = []

    lines.append('# SIRIUS %s MACHINE CONFIGURATION'%(machine.upper()))
    lines.append('# ==================================')
    lines.append('#')

    ts = timestamp.strftime('%Y-%m-%d %H:%M:%S') + '  (by sirius-save-machine-configuration.py)'
    lines.append('# TIMESTAMP ' + ts)
    lines.append('')

    # inserts PVs
    for pv_name in pvs:
        if 'FK-' not in pv_name:
            pv_name = 'VA-' + pv_name
            insert_new_pv(pv_name, lines)

    filename = machine.upper() + '_' + timestamp.strftime('%Y-%m-%d_%H-%M-%S')
    fname = os.path.join(_folder, filename + '.txt')
    try:
        f = open(fname, "w")
        for line in lines:
            print(line, file=f)
    except IOError:
        print('could not open file "' + fname + '"')


timestamp = datetime.datetime.fromtimestamp(time.time())
print('saving LI state'); save_state('li', timestamp); print()
print('saving TB state'); save_state('tb', timestamp); print()
print('saving BO state'); save_state('bo', timestamp); print()
print('saving TS state'); save_state('ts', timestamp); print()
print('saving SI state'); save_state('si', timestamp); print()
