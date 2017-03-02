from .LocalData import DeviceNames, RecordNames

_section = 'AS'
_el_names   = dict() # All these Family names must be defined in family_data dictionary
_fam_names  = dict() # All these Family names must be defined in family_data dictionary
_glob_names = dict() # These Family names can be any name
_inj_names = {
    'TI': ['Cycle',]
}
##### Excitation Curves #######
_excitation_curves_mapping = tuple()
##### Pulsed Magnets #######
_pulse_curve_mapping= dict()

device_names  = DeviceNames(_section, _el_names, _fam_names, _glob_names, _inj_names,
            _excitation_curves_mapping, _pulse_curve_mapping)

# build record names
record_names = RecordNames(device_names)

# --- Module API ---
get_all_record_names = record_names.get_all_record_names
get_database = record_names.get_database
get_read_only_pvs = record_names.get_read_only_pvs
get_read_write_pvs = record_names.get_read_write_pvs
get_dynamical_pvs = record_names.get_dynamical_pvs
get_constant_pvs = record_names.get_constant_pvs
