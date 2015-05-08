import sirius
import va.bo_fake_record_names

# subsystem dependent parameters
model = sirius.bo
fake_record_names = va.bo_fake_record_names.get_record_names()
def subsys(rn): return 'BO'+rn

fk = [] # [fake]
ps = [] # [power supply]
pa = [] # [parameters]
di = [] # [diagnostics]
di_bpms = []

record_names = model.record_names.get_record_names()
record_names = list(record_names.keys()) + list(fake_record_names.keys())
for record_name in record_names:
    if 'BPM-' in record_name:
        di_bpms.append(record_name)
    elif 'DI-' in record_name:
        di.append(record_name)
    elif 'PS-' in record_name:
        ps.append(record_name)
    elif 'PA-' in record_name:
        pa.append(record_name)
    elif 'FK-' in record_name:
        fk.append(record_name)
    else:
        print('Parameter', record_name, 'not found!')

read_only_pvs  = di_bpms + pa + di
read_write_pvs = ps + fk
dynamic_pvs = [subsys('DI-CURRENT'),
               subsys('DI-BCURRENT'),
              ]

database = {}
for p in di_bpms:
    database[p] = {'type' : 'float', 'count': 2}
for p in di:
    if any([substring in p for substring in ('BCURRENT',)]):
        database[p] = {'type' : 'float', 'count': model.harmonic_number, 'value': 0.0}
    else:
        database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
for p in ps:
    database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
for p in pa:
    if any([substring in p for substring in ('BLIFETIME',)]):
        database[p] = {'type' : 'float', 'count': model.harmonic_number, 'value': 0.0}
    else:
        database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
for p in fk:
    database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
