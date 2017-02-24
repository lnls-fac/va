from sirius import tb as model
from .LocalData import DeviceNames, RecordNames

_section = 'TB'
_el_names = { # All these Family names must be defined in family_data dictionary
    'DI': model.families.families_di(),
    'PS': ['CH','CV','QD1','QF1','QD2A','QF2A','QF2B',
           'QD2B','QF3','QD3','QF4','QD4','B'],
    'MA': ['CH','CV','QD1','QF1','QD2A','QF2A','QF2B',
           'QD2B','QF3','QD3','QF4','QD4','B'],
    'TI': ['InjS'],
    'PU': ['InjS'],
    'PM': ['InjS']
}
_fam_names = { # All these Family names must be defined in family_data dictionary
    'DI': ['BPM'],
    # 'PS': ['B'],
    'MA': ['B']
}
_glob_names = dict() # These Family names can be any name
_inj_names = dict()
##### Excitation Curves #######
_excitation_curves_mapping = {
    ('B',)  : 'tbma-b.txt',
    ('Q',)  : 'tbma-q.txt',
    ('CH',) : 'tbma-ch.txt',
    ('CV',) : 'tbma-cv.txt',
    ('InjS',)  : 'tbpm-injs.txt',
}
##### Pulsed Magnets #######
_pulse_curve_mapping= {
    'InjS':'tbpm-sep-pulse.txt' # INJECTION SEPTUM
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
