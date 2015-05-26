import sirius
import va.si_fake_record_names

# subsystem dependent parameters
model = sirius.si
fake_record_names = va.si_fake_record_names.get_record_names()
def subsys(rn): return 'SI'+rn

fk = [] # [fake]
pa = [] # [parameters]
di, di_bpms = [], [] # [diagnostics]
ps, ps_ch, ps_cv = [], [], [] # [power supply]

record_names = model.record_names.get_record_names()
record_names = list(record_names.keys()) + list(fake_record_names.keys())
for record_name in record_names:
    if 'DI-BPM-' in record_name:
        di_bpms.append(record_name)
    elif 'DI-' in record_name:
        di.append(record_name)
    elif 'PS-CH' in record_name:
        ps_ch.append(record_name)
    elif 'PS-CV' in record_name:
        ps_cv.append(record_name)
    elif 'PS-' in record_name:
        ps.append(record_name)
    elif 'PA-' in record_name:
        pa.append(record_name)
    elif 'FK-' in record_name:
        fk.append(record_name)
    else:
        print('Parameter', record_name, 'not found!')

read_only_pvs  = di_bpms + pa + di
read_write_pvs = ps + ps_ch + ps_cv + fk
dynamic_pvs = [subsys('DI-CURRENT'),
               subsys('DI-BCURRENT'),
              ]

ps = ps + ps_ch + ps_cv
di = di + di_bpms

database = {}

for p in di:
    if any([substring in p for substring in ('BCURRENT',)]):
        database[p] = {'type' : 'float', 'count': model.harmonic_number, 'value': 0.0}
    if 'DI-BPM' in p:
        if 'FAM' in p:
            database[p] = {'type' : 'float', 'count': 180}
        else:
            database[p] = {'type' : 'float', 'count': 2}
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
