from pymodels import ts as model
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
    'PS': ['B'],
    'MA': ['B']
}
_glob_names = dict() # These Family names can be any name
_inj_names = dict()
##### Excitation Curves #######
_excitation_curves_mapping = (
    (('B',)    , ('ts-dipole-b-fam.txt',1)),
    (('QD2',)  , ('ts-quadrupole-q14-qd.txt',1)),
    (('QD4A',) , ('ts-quadrupole-q14-qd.txt',1)),
    (('QD4B',) , ('ts-quadrupole-q14-qd.txt',1)),
    (('QF1A',) , ('ts-quadrupole-q14-qf.txt',1)),
    (('QF1B',) , ('ts-quadrupole-q14-qf.txt',1)),
    (('QF2',)  , ('ts-quadrupole-q20-qf.txt',1)),
    (('QF3',)  , ('ts-quadrupole-q20-qf.txt',1)),
    (('QF4',)  , ('ts-quadrupole-q20-qf.txt',1)),
    (('CH',)   , ('ts-corrector-ch.txt',1)),
    (('CV',)   , ('ts-corrector-cv.txt',1)),
    (('EjeSeptF',), ('ts-ejeseptum-thin.txt',1)),
    (('EjeSeptG',), ('ts-ejeseptum-thick.txt',1)),
    (('InjSeptG',), ('ts-injseptum-thick.txt',1)),
    (('InjSeptF',), ('ts-injseptum-thin.txt',1)),
)
##### Pulsed Magnets #######
_pulse_curve_mapping= {
    'InjSeptF':'ts-septum-injs.txt', # INJECTION SEPTUM
    'InjSeptG':'ts-septum-injs.txt', # INJECTION SEPTUM
    'EjeSeptF':'ts-septum-ejes.txt',
    'EjeSeptG':'ts-septum-ejes.txt',
}

device_names  = DeviceNames(_section, _el_names, _fam_names, _glob_names, _inj_names,
            _excitation_curves_mapping, _pulse_curve_mapping, model.get_family_data)


accelerator, *_ = model.create_accelerator()
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
