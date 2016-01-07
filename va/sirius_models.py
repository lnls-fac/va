
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
from . import model


# What about downstream accelerator prefixes?

class LiModel(linac_model.LinacModel):

    pv_module = _pvs_li
    prefix = pv_module.prefix
    model_module = pv_module.model
    database = pv_module.get_database()
    _downstream_accelerator_prefix = 'TB'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
    _emittance         = model_module.accelerator_data['emittance']
    _energy_spread     = model_module.accelerator_data['energy_spread']
    _global_coupling   = model_module.accelerator_data['global_coupling']
    _twiss_at_exit     = model_module.accelerator_data['twiss_at_exit'].make_dict()
    _pulse_duration    = model_module.pulse_duration_interval
    _frequency         = model_module.frequency
    _single_bunch_mode = 0
    nr_bunches         = int(_frequency*_pulse_duration/6)


class TbModel(tline_model.TLineModel):

    pv_module = _pvs_tb
    prefix = pv_module.prefix
    model_module = pv_module.model
    database = pv_module.get_database()
    nr_bunches = LiModel.nr_bunches
    _downstream_accelerator_prefix = 'BO'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)


class BoModel(booster_model.BoosterModel):

    pv_module = _pvs_bo
    prefix = pv_module.prefix
    model_module = pv_module.model
    database = pv_module.get_database()
    nr_bunches = model_module.harmonic_number
    _downstream_accelerator_prefix = 'TS'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
    _kickin_angle = model_module.accelerator_data['injection_kicker_nominal_deflection']
    _kickex_angle = model_module.accelerator_data['extraction_kicker_nominal_deflection']
    _injection_point_label = 'sept_in'
        

class TsModel(tline_model.TLineModel):

    pv_module = _pvs_ts
    prefix = pv_module.prefix
    model_module = pv_module.model
    database = pv_module.get_database()
    nr_bunches = BoModel.nr_bunches
    _downstream_accelerator_prefix = 'SI'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)


class SiModel(ring_model.RingModel):

    pv_module = _pvs_si
    prefix = pv_module.prefix
    model_module = pv_module.model
    database = pv_module.get_database()
    nr_bunches = model_module.harmonic_number
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
    _kickin_angle = model_module.accelerator_data['on_axis_kicker_nominal_deflection']
    _pmm_integ_polynom_b = model_module.accelerator_data['pmm_integ_polynom_b']
    _injection_point_label = 'eseptinf'
