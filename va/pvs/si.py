from pymodels import si as model
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
_excitation_curves_mapping = (
# This relation should be implemented and available from siriuspy/magnet !
    (('B1',)                             , ('si-dipole-b1.txt',+1)),
    (('B2',)                             , ('si-dipole-b2.txt',+1)),
    (('BC',)                             , ('si-dipole-bc.txt',+1)),
    (('QDA','QDB1','QDB2','QDP1','QDP2') , ('si-quadrupole-q14.txt',+1)),
    (('QFA','Q1','Q2','Q3','Q4')         , ('si-quadrupole-q20.txt',+1)),
    (('QFB','QFP')                       , ('si-quadrupole-q30.txt',+1)),
    (('QS',)                             , ('si-sextupole-s15-qs.txt',+1)),
    (('SFA0','SFA1','SFA2')              , ('si-sextupole-s15.txt',-1)),
    (('SFB0','SFB1','SFB2')              , ('si-sextupole-s15.txt',-1)),
    (('SFP0','SFP1','SFP2')              , ('si-sextupole-s15.txt',-1)),
    (('SDA0','SDA1','SDA2','SDA3')       , ('si-sextupole-s15.txt',+1)),
    (('SDB0','SDB1','SDB2','SDB3')       , ('si-sextupole-s15.txt',+1)),
    (('SDP0','SDP1','SDP2','SDP3')       , ('si-sextupole-s15.txt',+1)),
    (('CH',)                             , ('si-sextupole-s15-ch.txt',+1)),
    (('CV',)                             , ('si-sextupole-s15-cv.txt',+1)),
    ((('C2','CV','2'),)                  , ('bo-corrector-cv.txt',+1)), 
    (('FCH',)                            , ('si-corrector-fch.txt',+1)),
    (('FCV',)                            , ('si-corrector-fcv.txt',+1)),
    (('InjDpK',)                         , ('si-kicker-injdpk.txt',+1)),
    (('InjNLK',)                         , ('si-kicker-injnlk.txt',+1)),
    (('HPing',)                          , ('si-kicker-hping.txt',+1)),
    (('VPing',)                          , ('si-kicker-vping.txt',+1)),
)
##### Pulsed Magnets #######
_pulse_curve_mapping= {
    'HPing' :'si-kicker-hping.txt',
    'VPing' :'si-kicker-vping.txt',
    'InjDpK':'si-kicker-injdpk.txt',
    'InjNLK':'si-kicker-injnlk.txt',
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
