from siriuspy.namesys import SiriusPVName as _PVName
from va import pvs as _pvs

with open('VERSION','r') as _f:
    __version__ = _f.read().strip()

pvs_database = {
    'Version': {'type':'string', 'value':__version__},
}

area_structures = (_pvs.li,_pvs.tb,_pvs.bo,_pvs.ts,_pvs.si,_pvs.As)
for ArS in area_structures:
    ArS_database = ArS.record_names.get_database()
    for pv_name, value in ArS_database.items():
        # value.update({'scan':0.1})
        pv_name = _PVName(pv_name)
        if pv_name.discipline == 'DI' and pv_name.dev_type == 'BPM':
            pvs_database[pv_name] = value
