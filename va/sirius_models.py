
import sirius as _sirius
from .pvs import li as _pvs_li
from .pvs import tb as _pvs_tb
from .pvs import ts as _pvs_ts
from .pvs import bo as _pvs_bo
from .pvs import si as _pvs_si
from .pvs import ti as _pvs_ti
from . import tline_model   as _tline_model
from . import booster_model as _booster_model
from . import ring_model    as _ring_model
from . import timing_model  as _timing_model


class LiModel(_tline_model.TLineModel):

    prefix = 'LI'
    model_module = _sirius.li
    pv_module = _pvs_li
    database = _pvs_li.get_database()
    _downstream_accelerator_prefix = 'TB'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)

    _emittance         = model_module.accelerator_data['emittance']
    _energy_spread     = model_module.accelerator_data['energy_spread']
    _global_coupling   = model_module.accelerator_data['global_coupling']
    _twiss_at_exit     = model_module.accelerator_data['twiss_at_exit']
    _pulse_duration    = model_module.pulse_duration_interval[1]
    _frequency         = model_module.frequency
    _nr_bunches        = int(_frequency*_pulse_duration/6)
    _single_bunch_mode = True

class TbModel(_tline_model.TLineModel):

    prefix = 'TB'
    model_module = _sirius.tb
    pv_module = _pvs_tb
    database = _pvs_tb.get_database()
    _downstream_accelerator_prefix = 'BO'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
    _nr_bunches = _sirius.bo.harmonic_number

class BoModel(_booster_model.BoosterModel):

    prefix = 'BO'
    model_module = _sirius.bo
    pv_module = _pvs_bo
    database = _pvs_bo.get_database()
    _downstream_accelerator_prefix = 'TS'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
    _nr_bunches = model_module.harmonic_number

class TsModel(_tline_model.TLineModel):

    prefix = 'TS'
    model_module = _sirius.ts
    pv_module = _pvs_ts
    database = _pvs_ts.get_database()
    _downstream_accelerator_prefix = 'SI'
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
    _nr_bunches = _sirius.bo.harmonic_number

class SiModel(_ring_model.RingModel):

    prefix = 'SI'
    model_module = _sirius.si
    pv_module = _pvs_si
    database = _pvs_si.get_database()
    _delta_rx, _delta_angle = _sirius.coordinate_system.parameters(prefix)
    _nr_bunches = model_module.harmonic_number

class TiModel(_timing_model.TimingModel):

    prefix = 'TI'
    model_modelu = _sirius.ti
    pv_module = _pvs_ti
    database = _pvs_ti.get_database()
