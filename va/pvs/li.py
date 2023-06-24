from .models import lab_models
from .LocalData import DeviceNames, RecordNames


# PVs not connecting to real machine:
# ===================================
# LI-01:TI-EGun:Enbl-SP
# LI-01:TI-EGun:Enbl-RB
# LI-01:TI-EGun:Delay-SP
# LI-01:TI-EGun:Delay-RB


model = lab_models.li
_el_names = { # All these Family names must be defined in family_data dictionary
    'DI': [],  # model.families.families_di(),
    'RF': [],  # model.families.families_rf(),
#     'PS': ['Slnd01','Slnd02','Slnd03','Slnd04','Slnd05','Slnd06','Slnd07',
#            'Slnd08','Slnd09','Slnd10','Slnd11','Slnd12','Slnd13',
#            'QD1','QD2','QF3','CH','CV','Spect','Lens'],
    'PS': ['Slnd', 'QD1','QD2','QF3','CH','CV','Spect','Lens'],
    # 'MA': ['Slnd01','Slnd02','Slnd03','Slnd04','Slnd05','Slnd06','Slnd07',
    #        'Slnd08','Slnd09','Slnd10','Slnd11','Slnd12','Slnd13','Slnd14',
    #        'Slnd15','Slnd16','Slnd17','Slnd18','Slnd19','Slnd20','Slnd21',
    #        'QF1','QF2','QD1','QD2','QF3','CH','CV','Spect','Lens'],
    'MA': ['Slnd',
           'Slnd14','Slnd15','Slnd16','Slnd17','Slnd18','Slnd19','Slnd20','Slnd21',
           'QF1','QF2','QD1','QD2','QF3','CH','CV','Spect','Lens'],
    'TI': ['EGun'],
    # 'EG': ['EGun']
}
_fam_names = { # All these Family names must be defined in family_data dictionary
#     'PS': ['Slnd14','Slnd15','Slnd16','Slnd17','Slnd18','Slnd19','Slnd20',
#            'Slnd21','QF1','QF2'],
    'PS': ['QF1','QF2'],
    'MA': ['Slnd14','Slnd15','Slnd16','Slnd17','Slnd18','Slnd19','Slnd20',
           'Slnd21','QF1','QF2'],
}
_glob_names = dict() # These Family names can be any name
_inj_names = dict()
##### Excitation Curves #######
_excitation_curves_mapping = (
    (('QD',)  ,             ('li-quadrupole-long.txt',1)), # QD1 and QD2 !
    (('QF1','QF2', 'QF3') , ('li-quadrupole-short.txt',1)),
    (('CH',)       , ('li-corrector-ch-long.txt',1)), # Long and Short ?
    (('CV',)       , ('li-corrector-cv-long.txt',1)),
    (('Spect',)    , ('li-spect-45deg.txt',1)),
    (('Slnd',)     , ('li-solenoid-slnd.txt',1)),
    (('Lens',)     , ('li-lens.txt',1)),
)
##### Pulsed Magnets #######
_pulse_curve_mapping= dict()

device_names  = DeviceNames(model.section, _el_names, _fam_names, _glob_names, _inj_names,
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

