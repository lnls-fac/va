from sirius import si as model
from .LocalData import DeviceNames, RecordNames

_section = 'SI'
_el_names = { # All these Family names must be defined in family_data dictionary
    'DI': model.families.families_di(),
    'RF': model.families.families_rf(),
    'MA': (model.families.families_dipoles() +
           model.families.families_quadrupoles() +
           model.families.families_sextupoles() +
           model.families.families_horizontal_correctors() +
           model.families.families_vertical_correctors() +
           model.families.families_skew_correctors()
           ),
    'PS': (model.families.families_quadrupoles() +
           model.families.families_horizontal_correctors() +
           model.families.families_vertical_correctors() +
           model.families.families_skew_correctors()
           ),
    'PM': model.families.families_pulsed_magnets(),
    'PU': model.families.families_pulsed_magnets(),
    'TI': model.families.families_pulsed_magnets(),
}
_fam_names = { # All these Family names must be defined in family_data dictionary
    'PS': (['B1B2-1','B1B2-2']+
           model.families.families_quadrupoles() +
           model.families.families_sextupoles()
          ),
    'MA': (['B1B2-1','B1B2-2'] +
           model.families.families_quadrupoles() +
           model.families.families_sextupoles()
          ),
    'DI': ['BPM']
}
_glob_names = {# These Family names can be any name
    'AP': ['Tune','Chrom','CurrLT','BeamSz','Emit'],
}
_inj_names = dict()
##### Excitation Curves #######
_excitation_curves_mapping = {
    ('B1',)                     : 'sima-b1.txt',
    ('B2',)                     : 'sima-b2.txt',
    ('BC',)                     : 'sima-bc.txt',
    ('QD',)                     : 'sima-q14.txt',
    ('QFA','Q1','Q2','Q3','Q4') : 'sima-q20.txt',
    ('QFB','QFP')               : 'sima-q30.txt',
    ('QS',)                     : 'sima-qs.txt',
    ('SF',)                     : 'sima-sf.txt',
    ('SD',)                     : 'sima-sd.txt',
    ('CH',)                     : 'sima-ch.txt',
    ('CV',)                     : 'sima-cv.txt',
    ('FCH',)                    : 'sima-ch.txt',
    ('FCV',)                    : 'sima-cv.txt',
    ('InjDpK',)                 : 'sipm-injdpk.txt',
    ('InjNLK',)                 : 'sipm-injnlk.txt',
    ('VPing',)                  : 'sipm-injdpk.txt',
}
##### Pulsed Magnets #######
_pulse_curve_mapping= {
    'VPing' :'sipm-injdpk-pulse.txt',
    'InjDpK':'sipm-injdpk-pulse.txt',
    'InjNLK':'sipm-injnlk-pulse.txt',
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
