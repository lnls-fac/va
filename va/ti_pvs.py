import sirius
import va.ti_fake_record_names

# subsystem dependent parameters
model = sirius.ti
fake_record_names = va.ti_fake_record_names.get_record_names()
def subsys(rn): return 'TI'+rn

fk = [] # [fake]
pa = [] # [parameters]

all_record_names = {}
all_record_names.update(model.record_names.get_record_names())
all_record_names.update(fake_record_names)

record_names = model.record_names.get_record_names()
record_names = list(record_names.keys()) + list(fake_record_names.keys())
for record_name in record_names:
    if 'FK-' in record_name:
        fk.append(record_name)
    else:
        pa.append(record_name)

database = {}

for p in pa:
    database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
for p in fk:
    database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}

read_only_pvs  = []
read_write_pvs = pa + fk
dynamic_pvs = []
