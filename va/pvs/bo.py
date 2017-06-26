from pymodels import bo as model
from .LocalData import DeviceNames, RecordNames

_section = 'BO'
_el_names = { # All these Family names must be defined in family_data dictionary
    'DI': model.families.families_di(),
    'RF': model.families.families_rf(),
    'MA': ['B','QD','QF','SD','SF','QS','CH','CV'],
    'PS': ['QS','CH','CV'],
    'PM': ['InjK','EjeK'],
    'PU': ['InjK','EjeK'],
    'TI': ['InjK','EjeK'],
}
_fam_names = { # All these Family names must be defined in family_data dictionary
    'PS': ['B-1','B-2','QD','QF','SD','SF'],
    'MA': ['B-1','B-2','QD','QF','SD','SF']
}
_glob_names = {# These Family names can be any name
    'AP': ['Chrom','CurrLT','Size','Emitt'],
    'TI': ['STDMOE']
}
_inj_names = dict()
##### Excitation Curves #######
_excitation_curves_mapping = (
    (('B',)    , ('bo-dipole-b-fam.txt',1)),
    (('QF',)   , ('bo-quadrupole-qf-fam.txt',1)),
    (('QD',)   , ('bo-quadrupole-qd-fam.txt',1)),
    (('QS',)   , ('bo-quadrupole-qs.txt',1)),
    (('SF',)   , ('bo-sextupole-sf-fam.txt',1)),
    (('SD',)   , ('bo-sextupole-sd-fam.txt',1)),
    (('CH',)   , ('bo-corrector-ch.txt',1)),
    (('CV',)   , ('bo-corrector-cv.txt',1)),
    (('InjK',) , ('bo-injkicker.txt',1)),
    (('EjeK',) , ('bo-ejekicker.txt',1)),
)
##### Pulsed Magnets #######
_pulse_curve_mapping= {
    'EjeK':'bo-kicker-ejek.txt',
    'InjK':'bo-kicker-injk.txt',
}

device_names  = DeviceNames(_section, _el_names, _fam_names, _glob_names, _inj_names,
            _excitation_curves_mapping, _pulse_curve_mapping, model.get_family_data)


accelerator = model.create_accelerator()
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
