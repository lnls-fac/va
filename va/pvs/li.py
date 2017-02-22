from sirius import li as model
from .LocalData import DeviceNames, RecordNames

_section = 'LI'
_el_names = { # All these Family names must be defined in family_data dictionary
    'DI': model.families.families_di(),
    'RF': model.families.families_rf(),
    'PS': ['Slnd01','Slnd02','Slnd03','Slnd04','Slnd05','Slnd06','Slnd07',
           'Slnd08','Slnd09','Slnd10','Slnd11','Slnd12','Slnd13',
           'QD1','QD2','QF3','CH','CV','Spect','Lens'],
    'MA': ['Slnd01','Slnd02','Slnd03','Slnd04','Slnd05','Slnd06','Slnd07',
           'Slnd08','Slnd09','Slnd10','Slnd11','Slnd12','Slnd13','Slnd14',
           'Slnd15','Slnd16','Slnd17','Slnd18','Slnd19','Slnd20','Slnd21',
           'QF1','QF2','QD1','QD2','QF3','CH','CV','Spect','Lens'],
    'TI': ['EGun'],
    'EG': ['EGun']
}
_fam_names = { # All these Family names must be defined in family_data dictionary
    'PS': ['Slnd14','Slnd15','Slnd16','Slnd17','Slnd18','Slnd19','Slnd20',
           'Slnd21','QF1','QF2'],
    'MA': ['Slnd14','Slnd15','Slnd16','Slnd17','Slnd18','Slnd19','Slnd20',
           'Slnd21','QF1','QF2'],
}
_glob_names = dict() # These Family names can be any name
_inj_names = dict()
##### Excitation Curves #######
_excitation_curves_mapping = {
    ('QD','QF3'): 'lima-q.txt',
    ('QF',):      'lima-famqf.txt',
    ('CH',):      'lima-ch.txt',
    ('CV',):      'lima-cv.txt',
    ('Spect',):   'lima-spect.txt',
    ('Slnd',):    'lima-slnd.txt',
    ('Lens',):    'lima-lens.txt',
}
##### Pulsed Magnets #######
_pulse_curve_mapping= dict()

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
