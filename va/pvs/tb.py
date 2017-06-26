from pymodels import tb as model
from .LocalData import DeviceNames, RecordNames

_section = 'TB'
_el_names = { # All these Family names must be defined in family_data dictionary
    'DI': model.families.families_di(),
    'PS': ['CH','CV','QD1','QF1','QD2A','QF2A','QF2B',
           'QD2B','QF3','QD3','QF4','QD4'],
    'MA': ['CH','CV','QD1','QF1','QD2A','QF2A','QF2B',
           'QD2B','QF3','QD3','QF4','QD4','B'],
    'TI': ['InjS'],
    'PU': ['InjS'],
    'PM': ['InjS']
}
_fam_names = { # All these Family names must be defined in family_data dictionary
    'PS': ['B'],
    'MA': ['B']
}
_glob_names = dict() # These Family names can be any name
_inj_names = dict()
##### Excitation Curves #######
_excitation_curves_mapping = (
    (('B',)            , ('tb-dipole-b-fam.txt',1)),
    ((('01','B',''),)  , ('tb-dipole-b-fam.txt',-1)),
    (('Q',)            , ('tb-quadrupole.txt',1)),
    (('CH',)           , ('tb-corrector-ch.txt',1)),
    (('CV',)           , ('tb-corrector-cv.txt',1)),
    (('InjS',)         , ('tb-injseptum.txt',1)),
)
##### Pulsed Magnets #######
_pulse_curve_mapping= {
    'InjS':'tb-septum-injs.txt' # INJECTION SEPTUM
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
