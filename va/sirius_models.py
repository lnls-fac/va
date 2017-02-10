
import sirius as _sirius
from .pvs import li as _pvs_li
from .pvs import tb as _pvs_tb
from .pvs import bo as _pvs_bo
from .pvs import ts as _pvs_ts
from .pvs import si as _pvs_si
from . import linac_model
from . import tline_model
from . import booster_model
from . import ring_model

class LiModel(linac_model.LinacModel):

    pv_module = _pvs_li
    naming_system = _sirius.naming_system
    model_module = pv_module.model
    prefix = model_module.device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    _downstream_accelerator_prefix = 'TB'
    _delta_rx, _delta_angle        = _sirius.coordinate_system.parameters(prefix)
    _emittance                     = model_module.accelerator_data['emittance']
    _energy_spread                 = model_module.accelerator_data['energy_spread']
    _global_coupling               = model_module.accelerator_data['global_coupling']
    _twiss_at_exit                 = model_module.accelerator_data['twiss_at_exit'].make_dict()
    _frequency                     = model_module.frequency
    _single_bunch_charge           = model_module.single_bunch_charge
    _multi_bunch_charge            = model_module.multi_bunch_charge
    _single_bunch_pulse_duration   = model_module.single_bunch_pulse_duration
    _multi_bunch_pulse_duration    = model_module.multi_bunch_pulse_duration
    nr_bunches                     = int(_frequency*_multi_bunch_pulse_duration/6)


class TbModel(tline_model.TLineModel):

    pv_module = _pvs_tb
    naming_system = _sirius.naming_system
    model_module = pv_module.model
    prefix = model_module.device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    nr_bunches = LiModel.nr_bunches
    _downstream_accelerator_prefix = 'BO'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)


class BoModel(booster_model.BoosterModel):

    pv_module = _pvs_bo
    naming_system = _sirius.naming_system
    model_module = pv_module.model
    prefix = model_module.device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    nr_bunches = model_module.harmonic_number
    _downstream_accelerator_prefix = 'TS'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
    _injection_point_label  = 'InjS'
    _extraction_point_label = 'EjeSF'
    _ramp_interval          = 0.23


class TsModel(tline_model.TLineModel):

    pv_module = _pvs_ts
    naming_system = _sirius.naming_system
    model_module = pv_module.model
    prefix = model_module.device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    nr_bunches = BoModel.nr_bunches
    _downstream_accelerator_prefix = 'SI'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)


class SiModel(ring_model.RingModel):

    pv_module = _pvs_si
    naming_system = _sirius.naming_system
    model_module = pv_module.model
    prefix = model_module.device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    nr_bunches = model_module.harmonic_number
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
    _injection_point_label  = 'InjSF'
