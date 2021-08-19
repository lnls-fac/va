from .models import lab_models
from .LocalData import DeviceNames, RecordNames


# PVs not connecting to real machine:
# ===================================
# SI-13C4:DI-DCCT:BbBCurrent-Mon
# SI-13C4:DI-DCCT:HwFlt-Mon
# SI-13C4:DI-DCCT:CurrThold
# SI-14C4:DI-DCCT:BbBCurrent-Mon
# SI-14C4:DI-DCCT:HwFlt-Mon
# SI-14C4:DI-DCCT:CurrThold
# SI-Glob:AP-Tune
# SI-Glob:AP-Chrom
# SI-Glob:AP-CurrLT:CurrLT-Mon
# SI-Glob:AP-CurrLT:BbBCurrLT-Mon
# SI-Glob:AP-BeamSz
# SI-Glob:AP-Emit
# SI-03SP:RF-SRFCav:Freq-SP
# SI-03SP:RF-SRFCav:Freq-RB
# SI-03SP:RF-SRFCav:Volt-SP
# SI-03SP:RF-SRFCav:Volt-RB
# SI-01SA:TI-InjDpKckr:Enbl-SP
# SI-01SA:TI-InjDpKckr:Enbl-RB
# SI-01SA:TI-InjNLKckr:Enbl-SP
# SI-01SA:TI-InjNLKckr:Enbl-RB
# SI-01SA:TI-PingH:Enbl-SP
# SI-01SA:TI-PingH:Enbl-RB


model = lab_models.si
_el_names = { # All these Family names must be defined in family_data dictionary
    'DI': ['BPM', 'DCCT', # 'ScrapH', 'ScrapV', 'GSL15', 'GSL07',
           # 'GBPM', 'BbBPkup', 'BbBKckrH', 'BbBKckrV', 'BbBKckrL',
           # 'TuneShkrH', 'TuneShkrV', 'TunePkup',
          ],  # model.families.families_di(),
    'RF': model.families.families_rf(),
    'MA': (['B1', 'B2', ] +  # model.families.families_dipoles() +
           model.families.families_quadrupoles() +
           model.families.families_sextupoles() +
           ['CH', ] +  #  model.families.families_horizontal_correctors() +
           ['CV', ] +  #  model.families.families_vertical_correctors() +
           model.families.families_skew_correctors()
           ),
    'PS': (model.families.families_quadrupoles() +
           ['CH', ] +  #  model.families.families_horizontal_correctors() +
           ['CV', ] +  #  model.families.families_vertical_correctors() +
           model.families.families_skew_correctors()
           ),
    'PM': ['InjDpKckr', 'InjNLKckr', 'PingH'],  # 'PM': model.families.families_pulsed_magnets(),
    'PU': ['InjDpKckr', 'InjNLKckr', 'PingH'],  # 'PU': model.families.families_pulsed_magnets(),
    'TI': ['InjDpKckr', 'InjNLKckr', 'PingH'],  # 'TI': model.families.families_pulsed_magnets(),
}
_fam_names = { # All these Family names must be defined in family_data dictionary
    'PS': (['B1B2-1', 'B1B2-2'] +
           model.families.families_quadrupoles() +
           model.families.families_sextupoles()
          ),
    'MA': (['B1B2-1','B1B2-2']+
           model.families.families_quadrupoles() +
           model.families.families_sextupoles()
          ),
}
_glob_names = {# These Family names can be any name
    'AP': ['Tune','Chrom','CurrLT','BeamSz','Emit'],
}
_inj_names = dict()
##### Excitation Curves #######
_excitation_curves_mapping = (
# This relation should be implemented and available from siriuspy/magnet !
    (('B1',)                             , ('si-dipole-b1b2-fam.txt', +1)),
    (('B2',)                             , ('si-dipole-b1b2-fam.txt', +1)),
    (('QDA',)                            , ('si-quadrupole-q14-qda-fam.txt', +1)),
    (('QDB1',)                           , ('si-quadrupole-q14-qdb1-fam.txt', +1)),
    (('QDB2',)                           , ('si-quadrupole-q14-qdb2-fam.txt', +1)),
    (('QDP1',)                           , ('si-quadrupole-q14-qdp1-fam.txt', +1)),
    (('QDP2',)                           , ('si-quadrupole-q14-qdp2-fam.txt', +1)),
    (('QFA',)                            , ('si-quadrupole-q20-qfa-fam.txt', +1)),
    (('Q1',)                             , ('si-quadrupole-q20-q1-fam.txt', +1)),
    (('Q2',)                             , ('si-quadrupole-q20-q2-fam.txt', +1)),
    (('Q3',)                             , ('si-quadrupole-q20-q3-fam.txt', +1)),
    (('Q4',)                             , ('si-quadrupole-q20-q4-fam.txt', +1)),
    (('QFB',)                            , ('si-quadrupole-q30-qfb-fam.txt', +1)),
    (('QFP',)                            , ('si-quadrupole-q30-qfp-fam.txt', +1)),
    (('QS',)                             , ('si-sextupole-s15-qs.txt', +1)),
    (('SFA0', )                          , ('si-sextupole-s15-sfa0-fam.txt', +1)),
    (('SFA1', )                          , ('si-sextupole-s15-sfa1-fam.txt', +1)),
    (('SFA2', )                          , ('si-sextupole-s15-sfa2-fam.txt', +1)),
    (('SFB0', )                          , ('si-sextupole-s15-sfb0-fam.txt', +1)),
    (('SFB1', )                          , ('si-sextupole-s15-sfb1-fam.txt', +1)),
    (('SFB2', )                          , ('si-sextupole-s15-sfb2-fam.txt', +1)),
    (('SFP0', )                          , ('si-sextupole-s15-sfp0-fam.txt', +1)),
    (('SFP1', )                          , ('si-sextupole-s15-sfp1-fam.txt', +1)),
    (('SFP2', )                          , ('si-sextupole-s15-sfp2-fam.txt', +1)),
    (('SDA0', )                          , ('si-sextupole-s15-sda0-fam.txt', +1)),
    (('SDA1', )                          , ('si-sextupole-s15-sda1-fam.txt', +1)),
    (('SDA2', )                          , ('si-sextupole-s15-sda2-fam.txt', +1)),
    (('SDA3', )                          , ('si-sextupole-s15-sda3-fam.txt', +1)),
    (('SDB0', )                          , ('si-sextupole-s15-sdb0-fam.txt', +1)),
    (('SDB1', )                          , ('si-sextupole-s15-sdb1-fam.txt', +1)),
    (('SDB2', )                          , ('si-sextupole-s15-sdb2-fam.txt', +1)),
    (('SDB3', )                          , ('si-sextupole-s15-sdb3-fam.txt', +1)),
    (('SDP0', )                          , ('si-sextupole-s15-sdp0-fam.txt', +1)),
    (('SDP1', )                          , ('si-sextupole-s15-sdp1-fam.txt', +1)),
    (('SDP2', )                          , ('si-sextupole-s15-sdp2-fam.txt', +1)),
    (('SDP3', )                          , ('si-sextupole-s15-sdp3-fam.txt', +1)),
    (('CH',)                             , ('si-sextupole-s15-ch.txt', +1)),
    (('CV',)                             , ('si-sextupole-s15-cv.txt', +1)),
    ((('C2','CV','2'),)                  , ('bo-corrector-cv.txt', +1)),
    (('FCH',)                            , ('si-corrector-fch.txt', +1)),
    (('FCV',)                            , ('si-corrector-fcv.txt', +1)),
    (('PingH', )                         , ('si-hping.txt', +1)),
    # (('PingV', )                         , ('si-vping.txt', +1)),
    (('InjDpKckr',)                      , ('si-injdpk.txt', +1)),
    (('InjNLKckr',)                      , ('si-injnlk.txt', +1)),
)
##### Pulsed Magnets #######
_pulse_curve_mapping= {
    'PingH' :'si-kicker-hping.txt',
    # 'PingV' :'si-kicker-vping.txt',
    'InjDpKckr':'si-kicker-injdpk.txt',
    'InjNLKckr':'si-kicker-injnlk.txt',
}

device_names  = DeviceNames(
    model.section, _el_names, _fam_names, _glob_names, _inj_names,
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
