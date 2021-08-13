from .models import lab_models
from .LocalData import DeviceNames, RecordNames


# PVs not connecting to real machine:
# ===================================
# BO-35D:DI-DCCT:HwFlt-Mon
# BO-35D:DI-DCCT:BbBCurrent-Mon
# BO-35D:DI-DCCT:CurrThold
# BO-01D:DI-Scrn-2
# BO-02U:DI-Scrn
# BO-01D:DI-Scrn-1
# BO-04D:DI-TunePkup:Freq1-Mon
# BO-04D:DI-TunePkup:Freq2-Mon
# BO-04D:DI-TunePkup:Freq3-Mon
# BO-02D:DI-TuneShkr
# BO-04U:DI-GSL
# BO-Glob:AP-Chrom
# BO-Glob:AP-CurrLT:CurrLT-Mon
# BO-Glob:AP-CurrLT:BbBCurrLT-Mon
# BO-Glob:AP-Size
# BO-05D:RF-P5Cav:Freq-SP
# BO-05D:RF-P5Cav:Freq-RB
# BO-05D:RF-P5Cav:Volt-RB
# BO-05D:RF-P5Cav:Volt-SP
# BO-01D:TI-InjKckr:Enbl-SP
# BO-Glob:AP-Emitt
# BO-01D:TI-InjKckr:Enbl-RB
# BO-48D:TI-EjeKckr:Enbl-SP
# BO-48D:TI-EjeKckr:Enbl-RB
# BO-Glob:TI-STDMOE:Enbl-SP
# BO-Glob:TI-STDMOE:Enbl-RB
# BO-Glob:TI-STDMOE:Delay-SP
# BO-Glob:TI-STDMOE:Delay-RB


model = lab_models.bo
_el_names = { # All these Family names must be defined in family_data dictionary
    'DI': model.families.families_di(),
    'RF': model.families.families_rf(),
    'MA': ['B','QD','QF','SD','SF','QS','CH','CV'],
    'PS': ['QS','CH','CV'],
    'PM': ['InjKckr','EjeKckr'],
    'PU': ['InjKckr','EjeKckr'],
    'TI': ['InjKckr','EjeKckr'],
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
    (('InjKckr',) , ('bo-injkicker.txt',1)),
    (('EjeKckr',) , ('bo-ejekicker.txt',1)),
)
##### Pulsed Magnets #######
_pulse_curve_mapping= {
    'EjeKckr':'bo-kicker-ejek.txt',
    'InjKckr':'bo-kicker-injk.txt',
}

device_names  = DeviceNames(model.section, _el_names, _fam_names, _glob_names, _inj_names,
            _excitation_curves_mapping, _pulse_curve_mapping, model.get_family_data)


accelerator = model.create_accelerator()   # [150 MeV]
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
