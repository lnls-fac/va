
import sirius as _sirius
# from .pvs import li as _pvs_li
# from .pvs import tb as _pvs_tb
# from .pvs import ts as _pvs_ts
# from .pvs import bo as _pvs_bo
from .pvs import si as _pvs_si
# from .pvs import ti as _pvs_ti
# from .linac_model import LinacModel
# from .tline_model import TLineModel
# from .booster_model import BoosterModel
# from .ring_model import RingModel
# from .timing_model import TimingModel
from . import model
from .pvs import ma as _pvs_ma
from .pvs import mb as _pvs_mb


class ModelA(model.Model):

    prefix = 'MA'
    model_module = _sirius.si
    pv_module = _pvs_ma
    database = _pvs_ma.get_database()


class ModelB(model.Model):

    prefix = 'MB'
    model_module = _sirius.si
    pv_module = _pvs_mb
    database = _pvs_mb.get_database()


class SiModel(model.Model):

    pv_module = _pvs_si
    prefix = pv_module.prefix
    model_module = pv_module.model
    database = pv_module.get_database()

# class LiModel(LinacModel):
#
#     prefix = 'LI'
#     model_module = _sirius.li
#     pv_module = _pvs_li
#     database = _pvs_li.get_database()
#     _downstream_accelerator_prefix = 'TB'
#     _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
#     _emittance         = model_module.accelerator_data['emittance']
#     _energy_spread     = model_module.accelerator_data['energy_spread']
#     _global_coupling   = model_module.accelerator_data['global_coupling']
#     _twiss_at_exit     = model_module.accelerator_data['twiss_at_exit']
#     _pulse_duration    = model_module.pulse_duration_interval[1]
#     _frequency         = model_module.frequency
#     _single_bunch_mode = 0
#     nr_bunches         = int(_frequency*_pulse_duration/6)
#
#
# class TbModel(TLineModel):
#
#     prefix = 'TB'
#     model_module = _sirius.tb
#     pv_module = _pvs_tb
#     database = _pvs_tb.get_database()
#     nr_bunches = LiModel.nr_bunches
#     _downstream_accelerator_prefix = 'BO'
#     _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
#
# class BoModel(BoosterModel):
#
#     prefix = 'BO'
#     model_module = _sirius.bo
#     pv_module = _pvs_bo
#     database = _pvs_bo.get_database()
#     nr_bunches = model_module.harmonic_number
#     _downstream_accelerator_prefix = 'TS'
#     _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
#     _kickin_angle = model_module.accelerator_data['injection_kicker_nominal_deflection']
#     _kickex_angle = model_module.accelerator_data['extraction_kicker_nominal_deflection']
#
# class TsModel(TLineModel):
#
#     prefix = 'TS'
#     model_module = _sirius.ts
#     pv_module = _pvs_ts
#     database = _pvs_ts.get_database()
#     nr_bunches = BoModel.nr_bunches
#     _downstream_accelerator_prefix = 'SI'
#     _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
#
# class SiModel(RingModel):
#
#     prefix = 'SI'
#     model_module = _sirius.si
#     pv_module = _pvs_si
#     database = _pvs_si.get_database()
#     nr_bunches = model_module.harmonic_number
#     _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
#
#
# class TiModel(TimingModel):
#
#     prefix = 'TI'
#     model_module = _sirius.ti
#     pv_module = _pvs_ti
#     database = _pvs_ti.get_database()
#     _li_nr_bunches = LiModel.nr_bunches
