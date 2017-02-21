from sirius import ts as model
from .LocalData import DeviceNames, RecordNames

_section = 'TS'
_el_names = { # All these Family names must be defined in family_data dictionary
    'DI': model.families.families_di(),
    'PS': ['CH','CV','QF1A','QF1B','QD2','QF2','QF3',
           'QD4A','QF4','QD4B'],
    'MA': ['CH','CV','QF1A','QF1B','QD2','QF2','QF3',
           'QD4A','QF4','QD4B','B'],
    'TI': model.families.families_pulsed_magnets(),
    'PU': model.families.families_pulsed_magnets(),
    'PM': model.families.families_pulsed_magnets()
}
_fam_names = { # All these Family names must be defined in family_data dictionary
    'DI': ['BPM'],
    'PS': ['B'],
    'MA': ['B']
}
_glob_names = dict() # These Family names can be any name
_inj_names = dict()
##### Excitation Curves #######
_excitation_curves_mapping = {
    ('B',)    : 'tsma-b.txt',
    ('QF1',)  : 'tsma-q14.txt',
    ('QD',)   : 'tsma-q14.txt',
    ('QF',)   : 'tsma-q20.txt',
    ('CH',)   : 'tsma-ch.txt',
    ('CV',)   : 'tsma-cv.txt',
    ('EjeSF',): 'tspm-ejesf.txt',
    ('EjeSG',): 'tspm-ejesg.txt',
    ('InjSG',): 'tspm-injsg.txt',
    ('InjSF',): 'tspm-injsf.txt',
}
##### Pulsed Magnets #######
_pulse_curve_mapping= {
    'InjSF':'tspm-injs-pulse.txt', # INJECTION SEPTUM
    'InjSG':'tspm-injs-pulse.txt', # INJECTION SEPTUM
    'EjeSF':'tspm-ejes-pulse.txt',
    'EjeSG':'tspm-ejes-pulse.txt',
}

device_names  = DeviceNames(_section, _el_names, _fam_names, _glob_names, _inj_names,
            _excitation_curves_mapping, _pulse_curve_mapping, model.get_family_data)


accelerator,_ = model.create_accelerator()
family_data = model.get_family_data(accelerator)
# build record names
record_names = RecordNames(device_names, model, family_data)

# --- Module API ---
get_all_record_names = record_names.get_all_record_names
get_database = record_names.get_database
get_read_only_pvs = record_names.get_read_only_pvs
get_read_write_pvs = record_names.get_read_write_pvs
get_dynamical_pvs = record_names.get_dynamical_pvs
get_constant_pvs = record_names.get_constant_pvs
