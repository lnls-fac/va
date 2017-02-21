
import sirius as _sirius
from .pvs import li as _pvs_li
from .pvs import tb as _pvs_tb
from .pvs import bo as _pvs_bo
from .pvs import ts as _pvs_ts
from .pvs import si as _pvs_si
from . import accelerators_model
from . import area_structure


class ASModel(area_structure.AreaStructure):
    _first_accelerator_prefix = 'LI'


class LiModel(accelerators_model.LinacModel):

    pv_module = _pvs_li
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    _downstream_accelerator_prefix = 'TB'
    _delta_rx, _delta_angle        = 0.0, 0.0 #_sirius.coordinate_system.parameters(prefix)
    _emittance                     = model_module.accelerator_data['emittance']
    _energy_spread                 = model_module.accelerator_data['energy_spread']
    _global_coupling               = model_module.accelerator_data['global_coupling']
    _pulse_curves_dir              = model_module.accelerator_data['dirs']['pulse_curves']
    _excitation_curves_dir         = model_module.accelerator_data['dirs']['excitation_curves']
    _twiss_at_match                = model_module.accelerator_data['twiss_at_match'].make_dict()
    _frequency                     = model_module.frequency
    _single_bunch_charge           = model_module.single_bunch_charge
    _multi_bunch_charge            = model_module.multi_bunch_charge
    _single_bunch_pulse_duration   = model_module.single_bunch_pulse_duration
    _multi_bunch_pulse_duration    = model_module.multi_bunch_pulse_duration
    nr_bunches                     = int(_frequency*_multi_bunch_pulse_duration/6)


class TbModel(accelerators_model.TLineModel):

    pv_module = _pvs_tb
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    _pulse_curves_dir              = model_module.accelerator_data['dirs']['pulse_curves']
    _excitation_curves_dir         = model_module.accelerator_data['dirs']['excitation_curves']
    nr_bunches = LiModel.nr_bunches
    _downstream_accelerator_prefix = 'BO'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)


class BoModel(accelerators_model.BoosterModel):

    pv_module = _pvs_bo
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    nr_bunches = model_module.harmonic_number
    _downstream_accelerator_prefix = 'TS'
    _global_coupling               = model_module.accelerator_data['global_coupling']
    _pressure_profile              = model_module.accelerator_data['pressure_profile']
    _pulse_curves_dir              = model_module.accelerator_data['dirs']['pulse_curves']
    _excitation_curves_dir         = model_module.accelerator_data['dirs']['excitation_curves']
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
    _injection_point_label  = 'InjS'
    _extraction_point_label = 'EjeSF'
    _ramp_interval          = 0.23


class TsModel(accelerators_model.TLineModel):

    pv_module = _pvs_ts
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    _pulse_curves_dir              = model_module.accelerator_data['dirs']['pulse_curves']
    _excitation_curves_dir         = model_module.accelerator_data['dirs']['excitation_curves']
    nr_bunches = BoModel.nr_bunches
    _downstream_accelerator_prefix = 'SI'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)


class SiModel(accelerators_model.StorageRingModel):

    pv_module = _pvs_si
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    nr_bunches = model_module.harmonic_number
    _global_coupling               = model_module.accelerator_data['global_coupling']
    _pressure_profile              = model_module.accelerator_data['pressure_profile']
    _pulse_curves_dir              = model_module.accelerator_data['dirs']['pulse_curves']
    _excitation_curves_dir         = model_module.accelerator_data['dirs']['excitation_curves']
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
    _injection_point_label  = 'InjSF'
